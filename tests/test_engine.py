import json,sys,unittest,random,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import KB,ROOT,analyze,forward,backward,validate,HEADS,FACT_IDS
from server import prolog_analyze
SCENARIOS=json.loads((ROOT/'scenarios.json').read_text())
class EngineTests(unittest.TestCase):
 def test_requirement_counts(self):
  self.assertGreaterEqual(len(KB['facts']),20);self.assertGreaterEqual(len(KB['rules']),20)
 def test_unique_and_referenced_rules(self):
  self.assertEqual(len({r['id'] for r in KB['rules']}),len(KB['rules']))
  sources={s['id'] for s in KB['sources']}
  for r in KB['rules']:
   self.assertTrue(r['sources']);self.assertLessEqual(set(r['sources']),sources)
   self.assertTrue(r['conditions'])
   for c in r['conditions']:self.assertIn(c['fact'],FACT_IDS|HEADS)
 def test_scenarios(self):
  for s in SCENARIOS:
   with self.subTest(s['id']):
    a=analyze(dict(facts=s['facts']))
    self.assertEqual(a['priority'],s['expected_priority'])
    self.assertEqual(set(a['categories']),set(s['expected_categories']))
    self.assertLessEqual(set(s['expected_rules']),{t['rule'] for t in a['trace']})
 def test_every_rule_can_fire(self):
  def prerequisites(goal,path=()):
   if goal in FACT_IDS:return {goal:'yes'}
   if goal in path:raise AssertionError('Rule dependency cycle')
   r=next(r for r in KB['rules'] if r['conclusion']==goal)
   f={}
   for c in r['conditions']:
    if c['fact'] in FACT_IDS:f[c['fact']]=c['value']
    else:f.update(prerequisites(c['fact'],path+(goal,)))
   return f
  for r in KB['rules']:
   with self.subTest(r['id']):
    f={}
    for c in r['conditions']:
     if c['fact'] in FACT_IDS:f[c['fact']]=c['value']
     else:f.update(prerequisites(c['fact']))
    a=analyze(dict(facts=f,goal=r['conclusion']))
    self.assertIn(r['id'],[t['rule'] for t in a['trace']]);self.assertEqual(a['proof']['status'],'proven')
 def test_negative_is_not_unknown(self):
  self.assertEqual(backward('ransom_note',{})['status'],'unknown')
  self.assertEqual(backward('ransom_note',{'ransom_note':'no'})['status'],'not_supported')
  self.assertEqual(backward('ransom_note',{'ransom_note':'no'},'no')['status'],'proven')
 def test_unknown_backup_cannot_trigger_negative_rule(self):
  a=analyze(dict(facts={'files_encrypted':'yes','ransom_note':'yes'}))
  self.assertNotIn('action_recovery_gap',a['derived']);self.assertNotIn('action_recovery',a['derived'])
 def test_forward_rounds_and_trace(self):
  facts={'suspicious_email':'yes','suspicious_link':'yes','credentials_entered':'yes'}
  a=analyze(dict(facts=facts));w=dict(facts);last=0;pending={}
  for t in a['trace']:
   if t['round']!=last:w.update(pending);pending={};last=t['round']
   for c in t['conditions']:self.assertEqual(w.get(c['fact']),c['value'])
   self.assertTrue(t['explanation']);self.assertTrue(t['sources']);pending[t['conclusion']]='yes'
  self.assertGreater(last,2)
 def test_repeated_inputs_are_deterministic(self):
  f=SCENARIOS[1]['facts'];self.assertEqual(analyze(dict(facts=f)),analyze(dict(facts=f)))
 def test_new_case_does_not_inherit_facts(self):
  analyze(dict(facts=SCENARIOS[0]['facts']));self.assertEqual(analyze(dict(facts={}))['derived'],[])
 def test_all_unknown_and_all_no(self):
  for value in ['unknown','no']:
   a=analyze(dict(facts={k:value for k in FACT_IDS}));self.assertEqual(a['priority'],'unassessed');self.assertEqual(a['derived'],[])
 def test_reject_bad_input(self):
  for data in [[],{},dict(facts=[]),dict(facts={'invented':'yes'}),dict(facts={'malware_alert':True}),dict(facts={},goal='halt'),dict(facts={},extra=1)]:
   with self.subTest(data=data),self.assertRaises(ValueError):validate(data)
 def test_all_alternative_rules_are_recorded(self):
  a=analyze(dict(facts={'suspicious_email':'yes','sender_mismatch':'yes','suspicious_link':'yes'},goal='phishing'))
  self.assertLessEqual({'R01','R02'},{t['rule'] for t in a['trace']});self.assertEqual(len(a['proof']['alternatives']),2)
 def test_questions_are_relevant(self):
  a=analyze(dict(facts={'files_encrypted':'yes','ransom_note':'no'},goal='ransomware'))
  self.assertNotIn('ransom_note',a['questions']);self.assertIn('malware_alert',a['questions'])
 def test_forward_backward_equivalence(self):
  rng=random.Random(42)
  for i in range(100):
   facts={f['id']:rng.choice(['yes','no','unknown']) for f in KB['facts']};derived,_=forward(facts)
   for goal in HEADS:self.assertEqual(goal in derived,backward(goal,facts)['status']=='proven',goal)
 @unittest.skipUnless(shutil.which('swipl'),'SWI-Prolog is not installed')
 def test_prolog_python_parity(self):
  for s in SCENARIOS:
   for goal in HEADS:
    payload=dict(facts=s['facts'],goal=goal);a=analyze(payload);b=prolog_analyze(payload)
    for key in ['derived','trace','proof','priority','categories','questions']:self.assertEqual(a[key],b[key],(s['id'],goal,key))
if __name__=='__main__':unittest.main(verbosity=2)
