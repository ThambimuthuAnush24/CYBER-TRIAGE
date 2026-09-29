/** Browser edition of engine.py. Uses the same knowledge.json and three-valued proofs. */
export function createExpertSystem(knowledge) {
  // Keep consultation output and input changes from mutating the shared knowledge.
  const kb = structuredClone(knowledge);
  const factIds = new Set(kb.facts.map(f => f.id));
  const heads = new Set(kb.rules.map(r => r.conclusion));
  const goals = new Set([...factIds, ...heads]);
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);

  function validate(payload) {
    if (!object(payload) || Object.keys(payload).some(k => !['facts', 'goal'].includes(k))) {
      throw new Error('Request must contain only facts and optional goal.');
    }
    if (!object(payload.facts)) throw new Error('facts must be an object.');
    if (Object.keys(payload.facts).some(k => !factIds.has(k))) {
      throw new Error('Unrecognized observation name.');
    }
    if (Object.values(payload.facts).some(v => !['yes', 'no', 'unknown'].includes(v))) {
      throw new Error('Observations must be yes, no or unknown.');
    }
    const goal = Object.hasOwn(payload, 'goal') ? payload.goal : 'ransomware';
    if (typeof goal !== 'string' || !goals.has(goal)) throw new Error('Unrecognized goal.');
    return {facts: {...payload.facts}, goal};
  }

  function forward(facts) {
    const working = new Map(Object.entries(facts).filter(([, value]) => value !== 'unknown'));
    const fired = new Set();
    const trace = [];
    let round = 0;
    while (true) {
      // Construct the complete agenda before updating working memory for this round.
      const agenda = kb.rules.filter(r => !fired.has(r.id) &&
        r.conditions.every(c => working.get(c.fact) === c.value));
      if (!agenda.length) break;
      round += 1;
      for (const rule of agenda) {
        fired.add(rule.id);
        working.set(rule.conclusion, 'yes');
        trace.push({rule: rule.id, round, conclusion: rule.conclusion,
          conditions: rule.conditions, explanation: rule.explanation, sources: rule.sources});
      }
    }
    return {derived: [...heads].filter(h => working.get(h) === 'yes').sort(), trace};
  }

  function backward(goal, facts, value = 'yes', path = []) {
    if (path.includes(goal)) {
      return {goal, value, status: 'not_supported', reason: 'Cycle blocked', alternatives: []};
    }
    if (factIds.has(goal)) {
      const actual = Object.hasOwn(facts, goal) ? facts[goal] : 'unknown';
      const status = actual === 'unknown' ? 'unknown' : actual === value ? 'proven' : 'not_supported';
      return {goal, value, status, actual, alternatives: []};
    }
    const alternatives = kb.rules.filter(r => r.conclusion === goal).map(rule => {
      const children = rule.conditions.map(c => backward(c.fact, facts, c.value, [...path, goal]));
      const states = children.map(c => c.status);
      const status = states.includes('not_supported') ? 'not_supported' :
        states.includes('unknown') ? 'unknown' : 'proven';
      return {rule: rule.id, status, children};
    });
    const states = alternatives.map(a => a.status);
    const status = states.includes('proven') ? 'proven' :
      states.includes('unknown') ? 'unknown' : 'not_supported';
    return {goal, value, status, alternatives};
  }

  function analyze(payload) {
    const {facts, goal} = validate(payload);
    const {derived, trace} = forward(facts);
    const proof = backward(goal, facts);
    const priority = ['critical', 'high', 'medium'].find(p => derived.includes('priority_' + p)) || 'unassessed';
    const seen = new Set();
    const actions = [];
    for (const item of trace) {
      if (item.conclusion.startsWith('action_') && !seen.has(item.conclusion)) {
        actions.push({id: item.conclusion, text: item.explanation});
        seen.add(item.conclusion);
      }
    }
    const questions = new Set();
    function walk(node) {
      if (factIds.has(node.goal) && node.status === 'unknown') questions.add(node.goal);
      for (const alternative of node.alternatives || []) {
        if (alternative.status === 'unknown') alternative.children.forEach(walk);
      }
    }
    if (proof.status === 'unknown') walk(proof);
    return structuredClone({
      engine: 'Browser JavaScript rule engine', knowledge_version: kb.version,
      facts, goal, priority, categories: kb.categories.filter(c => derived.includes(c)),
      derived, trace, proof, questions: [...questions].sort(), actions,
      notice: 'Decision support only. Suspected categories require analyst validation. Unassessed does not mean safe. No containment actions are executed.'
    });
  }
  return Object.freeze({analyze});
}
