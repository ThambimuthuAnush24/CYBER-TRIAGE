"""Local-only UI adapter. No third-party Python packages required."""
import argparse,json,shutil,subprocess,sys
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
from engine import ROOT,KB,validate,assemble,analyze

def prolog_analyze(payload):
    facts,goal=validate(payload)
    result=subprocess.run(['swipl','-q','-s',str(ROOT/'prolog'/'main.pl')],input=json.dumps(payload),text=True,capture_output=True,cwd=ROOT,timeout=20)
    if result.returncode: raise RuntimeError('Prolog execution failed: '+result.stderr[:300])
    out=json.loads(result.stdout)
    return assemble(facts,goal,out['derived'],out['trace'],out['proof'],'SWI-Prolog')

class Handler(BaseHTTPRequestHandler):
    def send(self,status,data,ctype='application/json'):
        body=json.dumps(data).encode() if ctype=='application/json' else data
        self.send_response(status);self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'")
        self.end_headers();self.wfile.write(body)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/meta': return self.send(200,dict(kb=KB,scenarios=json.loads((ROOT/'scenarios.json').read_text()),engine=self.server.engine_name))
        routes={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
        if path not in routes:return self.send(404,dict(error='Not found'))
        name=routes[path]; types={'html':'text/html; charset=utf-8','js':'text/javascript; charset=utf-8','css':'text/css; charset=utf-8'}
        self.send(200,(ROOT/'web'/name).read_bytes(),types[name.split('.')[-1]])
    def do_POST(self):
        if urlsplit(self.path).path!='/api/analyze':return self.send(404,dict(error='Not found'))
        origin=self.headers.get('Origin')
        if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'):
            return self.send(403,dict(error='Cross-origin requests are not accepted.'))
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,dict(error='Use application/json.'))
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=16384:raise ValueError('Request size must be 1 to 16384 bytes.')
            def unique(pairs):
                d={}
                for k,v in pairs:
                    if k in d:raise ValueError('Duplicate keys are not accepted.')
                    d[k]=v
                return d
            payload=json.loads(self.rfile.read(size),object_pairs_hook=unique)
            self.send(200,self.server.infer(payload))
        except (ValueError,UnicodeError) as e:self.send(400,dict(error=str(e)))
        except (RuntimeError,subprocess.TimeoutExpired) as e:self.send(503,dict(error=str(e)))
    def log_message(self,fmt,*args): pass # Do not record incident input in logs.

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['auto','prolog','python'],default='auto');parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args();available=shutil.which('swipl') is not None
    if args.engine=='prolog' and not available:sys.exit('SWI-Prolog not found. Install it and add swipl to PATH, or use --engine python for the portable edition.')
    use_prolog=args.engine=='prolog' or (args.engine=='auto' and available)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    server.infer=prolog_analyze if use_prolog else analyze
    server.engine_name='SWI-Prolog' if use_prolog else 'Portable Python rule shell'
    print(f'Cyber Triage | {server.engine_name} | http://127.0.0.1:{args.port}',flush=True)
    print('Press Ctrl+C to stop. Cases are held in browser memory only.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
