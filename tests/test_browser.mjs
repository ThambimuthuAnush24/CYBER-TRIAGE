import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {createServer} from 'node:http';
import {once} from 'node:events';
import {createExpertSystem} from '../web/engine.mjs';
import {loadRuntime} from '../web/runtime.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const read = path => readFileSync(resolve(root, path), 'utf8');
const kb = JSON.parse(read('knowledge.json'));
const scenarios = JSON.parse(read('scenarios.json'));
const facts = kb.facts.map(f => f.id);
const factIds = new Set(facts);
const goals = [...new Set([...facts, ...kb.rules.map(r => r.conclusion)])];
const engine = createExpertSystem(kb);
const python = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const pythonRun = (code, input) => execFileSync(python, ['-c', code], {
  cwd: root, encoding: 'utf8', input, maxBuffer: 16 * 1024 * 1024
});

test('all 12 scenarios retain their independent expected outcomes', async t => {
  for (const scenario of scenarios) {
    await t.test(scenario.id + ': ' + scenario.name, () => {
      const result = engine.analyze({facts: scenario.facts});
      assert.equal(result.priority, scenario.expected_priority);
      assert.deepEqual(new Set(result.categories), new Set(scenario.expected_categories));
      for (const id of scenario.expected_rules) {
        assert.ok(result.trace.some(row => row.rule === id), 'Expected rule ' + id);
      }
    });
  }
});

test('every production rule can fire and prove its conclusion', () => {
  function prerequisites(goal, path = []) {
    if (factIds.has(goal)) return {[goal]: 'yes'};
    assert.ok(!path.includes(goal), 'Dependency cycle at ' + goal);
    const rule = kb.rules.find(r => r.conclusion === goal);
    assert.ok(rule, 'Missing rule for ' + goal);
    return conditions(rule, [...path, goal]);
  }
  function conditions(rule, path = []) {
    return Object.assign({}, ...rule.conditions.map(c => factIds.has(c.fact)
      ? {[c.fact]: c.value} : prerequisites(c.fact, path)));
  }
  for (const rule of kb.rules) {
    const result = engine.analyze({facts: conditions(rule), goal: rule.conclusion});
    assert.ok(result.trace.some(row => row.rule === rule.id), rule.id + ' did not fire');
    assert.equal(result.proof.status, 'proven', rule.id + ' could not prove its goal');
  }
});

test('complete results match Python for 115 evidence sets across all 54 goals', t => {
  const cases = [
    ...scenarios.map(s => s.facts), {},
    Object.fromEntries(facts.map(f => [f, 'unknown'])),
    Object.fromEntries(facts.map(f => [f, 'no']))
  ];
  let seed = 42;
  function randomValue() {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return ['yes', 'no', 'unknown'][seed % 3];
  }
  for (let i = 0; i < 100; i++) cases.push(Object.fromEntries(facts.map(f => [f, randomValue()])));
  const payloads = cases.flatMap(evidence => goals.map(goal => ({facts: evidence, goal})));
  // Hash canonical full results to keep the Python/Node bridge small. Engine labels
  // intentionally differ; every other field, including complete proofs, is compared.
  const expected = JSON.parse(pythonRun(`
import hashlib, json, sys
from engine import analyze
digests = []
for payload in json.load(sys.stdin):
    result = analyze(payload)
    del result['engine']
    encoded = json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    digests.append(hashlib.sha256(encoded).hexdigest())
json.dump(digests, sys.stdout)
`, JSON.stringify(payloads)));
  function canonical(value) {
    if (Array.isArray(value)) return value.map(canonical);
    if (value !== null && typeof value === 'object') {
      return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])]));
    }
    return value;
  }
  assert.equal(expected.length, payloads.length);
  payloads.forEach((payload, i) => {
    const result = engine.analyze(payload);
    delete result.engine;
    const digest = createHash('sha256').update(JSON.stringify(canonical(result))).digest('hex');
    assert.equal(digest, expected[i], 'Full output mismatch for ' + JSON.stringify(payload));
  });
  t.diagnostic(`${payloads.length} complete result comparisons passed.`);
});

test('Unknown never satisfies No, including backup recovery rules', () => {
  const evidence = {files_encrypted: 'yes', ransom_note: 'yes'};
  for (const backup of [undefined, 'unknown', 'no', 'yes']) {
    const result = engine.analyze({facts: {...evidence, ...(backup ? {backup_available: backup} : {})}});
    assert.equal(result.derived.includes('action_recovery_gap'), backup === 'no');
    assert.equal(result.derived.includes('action_recovery'), backup === 'yes');
  }
  assert.equal(engine.analyze({facts: {}, goal: 'ransom_note'}).proof.status, 'unknown');
  assert.equal(engine.analyze({facts: {ransom_note: 'no'}, goal: 'ransom_note'}).proof.status, 'not_supported');
});

test('invalid payloads are rejected before inference', () => {
  for (const payload of [null, [], {}, {facts: null}, {facts: []},
    {facts: {invented: 'yes'}}, {facts: {malware_alert: true}},
    {facts: {malware_alert: 'YES'}}, {facts: {}, goal: null},
    {facts: {}, goal: 'halt'}, {facts: {}, extra: 1}]) {
    assert.throws(() => engine.analyze(payload), Error);
  }
});

test('case and returned-result changes cannot contaminate later consultations', () => {
  const payload = {facts: structuredClone(scenarios[0].facts)};
  const expected = engine.analyze(payload);
  const result = engine.analyze(payload);
  result.trace[0].conditions[0].value = 'no';
  result.trace[0].sources.push('invented');
  result.facts.files_encrypted = 'no';
  assert.deepEqual(engine.analyze(payload), expected);
  payload.facts.files_encrypted = 'no';
  assert.equal(expected.facts.files_encrypted, 'yes');
  assert.deepEqual(engine.analyze({facts: {}}).derived, []);
});

test('server mode retains its API transport and propagates analysis errors', async () => {
  const requests = [];
  const mock = async (url, options) => {
    requests.push({url: String(url), options});
    if (url.pathname.endsWith('/api/meta')) return {ok: true, json: async () => ({kb, scenarios})};
    if (JSON.parse(options.body).goal === 'invalid') {
      return {ok: false, json: async () => ({error: 'Unrecognized goal.'})};
    }
    return {ok: true, json: async () => ({priority: 'critical'})};
  };
  const runtime = await loadRuntime('server', 'http://localhost:8000/', mock);
  const payload = {facts: scenarios[0].facts};
  assert.equal((await runtime.analyze(payload)).priority, 'critical');
  assert.equal(requests[0].url, 'http://localhost:8000/api/meta');
  assert.equal(requests[1].url, 'http://localhost:8000/api/analyze');
  assert.equal(requests[1].options.method, 'POST');
  assert.deepEqual(JSON.parse(requests[1].options.body), payload);
  await assert.rejects(runtime.analyze({facts: {}, goal: 'invalid'}), /Unrecognized goal/);
});

test('configuration and missing static-data errors remain visible', async () => {
  const missing = async () => ({ok: false, status: 404});
  await assert.rejects(loadRuntime('browser', 'https://example.github.io/repo/', missing), /HTTP 404/);
  await assert.rejects(loadRuntime('invalid', 'https://example.github.io/repo/', missing), /Unknown application mode/);
});

test('static build works over HTTP at a repository subpath without analysis requests', async t => {
  execFileSync(python, ['scripts/build_pages.py'], {cwd: root, encoding: 'utf8'});
  const assets = ['.nojekyll', 'index.html', 'app.js', 'style.css', 'engine.mjs', 'runtime.mjs', 'knowledge.json', 'scenarios.json'];
  assert.deepEqual(readdirSync(resolve(root, 'dist')).sort(), [...assets].sort());
  const html = read('dist/index.html');
  assert.match(html, /data-mode="browser"/);
  assert.match(html, /type="module" src="\.\/app\.js"/);
  assert.match(html, /href="\.\/style\.css"/);
  assert.match(read('web/index.html'), /data-mode="server"/);
  for (const name of assets.filter(n => !['.nojekyll', 'index.html'].includes(n))) {
    const original = name.endsWith('.json') ? name : 'web/' + name;
    assert.equal(read('dist/' + name), read(original), 'Build changed source asset ' + name);
  }
  const requests = [];
  const types = {html: 'text/html', js: 'text/javascript', mjs: 'text/javascript', css: 'text/css', json: 'application/json'};
  const server = createServer((request, response) => {
    requests.push({method: request.method, url: request.url});
    const prefix = '/cyber-triage/';
    const name = request.url.startsWith(prefix) ? request.url.slice(prefix.length) || 'index.html' : '';
    if (request.method !== 'GET' || !assets.includes(name)) {response.writeHead(404).end(); return;}
    response.setHeader('Content-Type', types[name.split('.').at(-1)] || 'text/plain');
    response.end(read('dist/' + name));
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  t.after(() => new Promise((done, reject) => server.close(error => error ? reject(error) : done())));
  const base = `http://127.0.0.1:${server.address().port}/cyber-triage/`;
  for (const asset of ['', 'app.js', 'style.css', 'engine.mjs', 'runtime.mjs']) {
    const response = await fetch(new URL(asset, base));
    assert.equal(response.status, 200, asset);
    assert.ok((await response.text()).length > 0);
  }
  const runtime = await loadRuntime('browser', base);
  assert.equal(runtime.meta.kb.rules.length, 42);
  assert.equal(runtime.meta.scenarios.length, 12);
  const beforeAnalysis = requests.length;
  for (const scenario of scenarios) {
    assert.equal((await runtime.analyze({facts: scenario.facts})).priority, scenario.expected_priority);
  }
  assert.equal(requests.length, beforeAnalysis, 'Browser inference sent a network request');
  assert.ok(requests.every(r => r.method === 'GET' && !r.url.includes('/api/')));
  assert.deepEqual(requests.slice(-2).map(r => r.url).sort(), ['/cyber-triage/knowledge.json', '/cyber-triage/scenarios.json']);
});
