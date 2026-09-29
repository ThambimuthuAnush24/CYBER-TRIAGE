import {createExpertSystem} from './engine.mjs';

/** Explicit mode selection avoids sending incident evidence to an absent Pages API. */
export async function loadRuntime(mode, baseURL, request = globalThis.fetch.bind(globalThis)) {
  async function json(path, options) {
    const response = await request(new URL(path, baseURL), options);
    if (!response.ok) throw new Error('Unable to load ' + path + ' (HTTP ' + response.status + ').');
    return response.json();
  }
  if (mode === 'browser') {
    const [kb, scenarios] = await Promise.all([json('./knowledge.json'), json('./scenarios.json')]);
    const engine = createExpertSystem(kb);
    return {
      meta: {kb, scenarios, engine: 'Browser JavaScript rule engine'},
      analyze: payload => engine.analyze(payload)
    };
  }
  if (mode !== 'server') throw new Error('Unknown application mode.');
  const meta = await json('./api/meta');
  return {meta, analyze: async payload => {
    const response = await request(new URL('./api/analyze', baseURL), {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Analysis failed');
    return data;
  }};
}
