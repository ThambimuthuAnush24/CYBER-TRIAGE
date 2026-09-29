"""Portable, deterministic production-rule shell. SWI-Prolog is the preferred engine."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
KB=json.loads((ROOT/'knowledge.json').read_text())
FACT_IDS={f['id'] for f in KB['facts']}
HEADS={r['conclusion'] for r in KB['rules']}
GOALS=FACT_IDS|HEADS

def validate(payload):
    if not isinstance(payload,dict) or set(payload)-{'facts','goal'}:
        raise ValueError('Request must contain only facts and optional goal.')
    facts=payload.get('facts')
    if not isinstance(facts,dict): raise ValueError('facts must be an object.')
    if set(facts)-FACT_IDS: raise ValueError('Unrecognized observation name.')
    if any(type(v) is not str or v not in ('yes','no','unknown') for v in facts.values()):
        raise ValueError('Observations must be yes, no or unknown.')
    goal=payload.get('goal','ransomware')
    if not isinstance(goal,str) or goal not in GOALS: raise ValueError('Unrecognized goal.')
    return dict(facts),goal

def forward(facts):
    working={k:v for k,v in facts.items() if v!='unknown'}
    fired=set(); trace=[]; round_no=0
    while True:
        agenda=[r for r in KB['rules'] if r['id'] not in fired and all(working.get(c['fact'])==c['value'] for c in r['conditions'])]
        if not agenda: break
        round_no+=1
        for r in agenda:
            fired.add(r['id']); working[r['conclusion']]='yes'
            trace.append(dict(rule=r['id'],round=round_no,conclusion=r['conclusion'],conditions=r['conditions'],explanation=r['explanation'],sources=r['sources']))
    return sorted(k for k in HEADS if working.get(k)=='yes'),trace

def backward(goal,facts,value='yes',path=()):
    if goal in path: return dict(goal=goal,value=value,status='not_supported',reason='Cycle blocked',alternatives=[])
    if goal in FACT_IDS:
        actual=facts.get(goal,'unknown')
        status='unknown' if actual=='unknown' else ('proven' if actual==value else 'not_supported')
        return dict(goal=goal,value=value,status=status,actual=actual,alternatives=[])
    alternatives=[]
    for r in KB['rules']:
        if r['conclusion']!=goal: continue
        children=[backward(c['fact'],facts,c['value'],path+(goal,)) for c in r['conditions']]
        states=[c['status'] for c in children]
        status='not_supported' if 'not_supported' in states else ('unknown' if 'unknown' in states else 'proven')
        alternatives.append(dict(rule=r['id'],status=status,children=children))
    states=[a['status'] for a in alternatives]
    status='proven' if 'proven' in states else ('unknown' if 'unknown' in states else 'not_supported')
    return dict(goal=goal,value=value,status=status,alternatives=alternatives)

def assemble(facts,goal,derived,trace,proof,engine):
    priority=next((p for p in ['critical','high','medium'] if 'priority_'+p in derived),'unassessed')
    actions=[]; seen=set()
    for t in trace:
        if t['conclusion'].startswith('action_') and t['conclusion'] not in seen:
            actions.append(dict(id=t['conclusion'],text=t['explanation']));seen.add(t['conclusion'])
    questions=set()
    def walk(n):
        if n['goal'] in FACT_IDS and n['status']=='unknown': questions.add(n['goal'])
        for a in n.get('alternatives',[]):
            if a['status']=='unknown':
                for c in a['children']: walk(c)
    if proof['status']=='unknown':walk(proof)
    return dict(engine=engine,knowledge_version=KB['version'],facts=facts,goal=goal,priority=priority,categories=[c for c in KB['categories'] if c in derived],derived=derived,trace=trace,proof=proof,questions=sorted(questions),actions=actions,notice='Decision support only. Suspected categories require analyst validation. Unassessed does not mean safe. No containment actions are executed.')

def analyze(payload):
    facts,goal=validate(payload); derived,trace=forward(facts)
    return assemble(facts,goal,derived,trace,backward(goal,facts),'Portable Python rule shell')

if __name__=='__main__':
    import sys
    print(json.dumps(analyze(json.load(sys.stdin)),indent=2))
