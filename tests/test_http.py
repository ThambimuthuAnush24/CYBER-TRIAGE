import json,sys,unittest,threading,urllib.request,urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import Handler,ThreadingHTTPServer
from engine import analyze
class HTTPTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);cls.server.infer=analyze;cls.server.engine_name='Portable Python rule shell'
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
  cls.base='http://127.0.0.1:'+str(cls.server.server_port);cls.client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
 def request(self,path,body=None,headers=None):
  req=urllib.request.Request(self.base+path,data=body,headers=headers or {})
  try:r=self.client.open(req,timeout=5)
  except urllib.error.HTTPError as e:r=e
  with r:return r.code,r.read(),r.headers
 def test_interface_assets(self):
  for path in ['/','/app.js','/style.css','/engine.mjs','/runtime.mjs','/api/meta']:
   code,body,h=self.request(path);self.assertEqual(code,200);self.assertTrue(body);self.assertIn('Content-Security-Policy',h)
 def test_post_analysis(self):
  code,body,_=self.request('/api/analyze',b'{"facts":{"malware_alert":"yes"}}',{'Content-Type':'application/json'})
  self.assertEqual(code,200);self.assertEqual(json.loads(body)['priority'],'high')
 def test_bad_json(self):
  self.assertEqual(self.request('/api/analyze',b'{',{'Content-Type':'application/json'})[0],400)
 def test_duplicate_keys(self):
  self.assertEqual(self.request('/api/analyze',b'{"facts":{"malware_alert":"yes","malware_alert":"no"}}',{'Content-Type':'application/json'})[0],400)
 def test_bad_type(self):
  self.assertEqual(self.request('/api/analyze',b'{}',{'Content-Type':'text/plain'})[0],415)
 def test_origin_rejected(self):
  self.assertEqual(self.request('/api/analyze',b'{"facts":{}}',{'Content-Type':'application/json','Origin':'https://example.invalid'})[0],403)
 def test_oversized_input(self):
  self.assertEqual(self.request('/api/analyze',b' '*17000,{'Content-Type':'application/json'})[0],400)
 def test_missing_and_traversal(self):
  for path in ['/missing','/../knowledge.json','/server.py']:
   self.assertEqual(self.request(path)[0],404)
