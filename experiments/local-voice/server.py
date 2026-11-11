#!/usr/bin/env python3
"""Offline-only ASR demo. Loopback-only HTTP. NO device control in M0."""
import ctypes, json, os
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from threading import Lock
from time import monotonic
ROOT=Path(__file__).resolve().parent
MODEL=ROOT/'model'/'vosk-model-small-cn-0.22'
WEB=ROOT/'web'
MAX_AUDIO=16000*2*9
lock=Lock()

def load_model():
    v=ctypes.CDLL(str(ROOT/'libvosk.so'))
    v.vosk_set_log_level.argtypes=[ctypes.c_int]
    v.vosk_model_new.argtypes=[ctypes.c_char_p]
    v.vosk_model_new.restype=ctypes.c_void_p
    v.vosk_model_free.argtypes=[ctypes.c_void_p]
    v.vosk_recognizer_new.argtypes=[ctypes.c_void_p,ctypes.c_float]
    v.vosk_recognizer_new.restype=ctypes.c_void_p
    v.vosk_recognizer_free.argtypes=[ctypes.c_void_p]
    v.vosk_recognizer_accept_waveform.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int]
    v.vosk_recognizer_accept_waveform.restype=ctypes.c_int
    v.vosk_recognizer_final_result.argtypes=[ctypes.c_void_p]
    v.vosk_recognizer_final_result.restype=ctypes.c_char_p
    v.vosk_set_log_level(-1)
    model=v.vosk_model_new(os.fsencode(str(MODEL)))
    if not model:raise RuntimeError('failed to load offline Chinese model')
    return v,model

def intent(text):
    s=''.join(c for c in text if c not in ' ,，。！？!?.\n\t')
    if not s:return {'matched':False,'reason':'没有识别到声音'}
    targets=[('客厅灯',('客厅','灯')),('卧室灯',('卧室','灯')),('窗帘',('窗帘',)),('空调',('空调',)),('灯',('灯',))]
    target=next((name for name,words in targets if all(w in s for w in words)),None)
    on=any(w in s for w in ('打开','开启','开灯','升起'))
    off=any(w in s for w in ('关闭','关掉','关灯','合上'))
    if not target or on==off:return {'matched':False,'reason':'未匹配到明确指令'}
    return {'matched':True,'target':target,'action':'turn_on' if on else 'turn_off','executed':False}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,format,*args):
        # No transcripts, audio, query parameters or tokens in logs.
        print('REQUEST',self.command,self.path.split('?')[0],flush=True)
    def send(self,data,status=200,kind='application/json; charset=utf-8'):
        if not isinstance(data,str):data=json.dumps(data,ensure_ascii=False)
        raw=data.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'")
        self.end_headers();self.wfile.write(raw)
    def allowed(self):return self.headers.get('Host') in ('127.0.0.1:8126','localhost:8126')
    def do_GET(self):
        if not self.allowed():return self.send({'error':'loopback_only'},403)
        p=self.path.split('?')[0]
        if p=='/health':return self.send({'ready':True,'offline':True,'actions_enabled':False})
        if p in ('/','/index.html'):return self.send((WEB/'index.html').read_text(encoding='utf-8'),kind='text/html; charset=utf-8')
        if p=='/app.js':return self.send((WEB/'app.js').read_text(encoding='utf-8'),kind='application/javascript; charset=utf-8')
        return self.send({'error':'not_found'},404)
    def do_POST(self):
        if not self.allowed():return self.send({'error':'loopback_only'},403)
        if self.path!='/recognize':return self.send({'error':'not_found'},404)
        if self.headers.get('Content-Type','').split(';')[0].strip()!='application/octet-stream':return self.send({'error':'invalid_type'},415)
        try:n=int(self.headers.get('Content-Length','0'))
        except ValueError:return self.send({'error':'invalid_length'},400)
        if not 3200<=n<=MAX_AUDIO or n%2:return self.send({'error':'invalid_length'},400)
        data=self.rfile.read(n)
        if len(data)!=n:return self.send({'error':'incomplete_audio'},400)
        t0=monotonic()
        try:
            with lock:
                rec=self.server.v.vosk_recognizer_new(self.server.model,16000.)
                if not rec:raise RuntimeError('recognizer init failed')
                try:
                    a=ctypes.create_string_buffer(data)
                    self.server.v.vosk_recognizer_accept_waveform(rec,a,n)
                    result=json.loads(self.server.v.vosk_recognizer_final_result(rec).decode('utf-8'))
                finally:self.server.v.vosk_recognizer_free(rec)
            t=result.get('text','')
            return self.send({'text':t,'intent':intent(t),'elapsed_ms':round(1000*(monotonic()-t0)),'offline':True,'executed':False})
        except Exception as e:
            print('ASR_ERROR',type(e).__name__,flush=True)
            return self.send({'error':'recognizer_failed'},500)

def main():
    print('LOADING_OFFLINE_VOSK_MODEL',flush=True)
    v,model=load_model()
    server=ThreadingHTTPServer(('127.0.0.1',8126),Handler)
    server.v=v;server.model=model
    print('VOICE_LAB_READY http://127.0.0.1:8126/ no_cloud no_actions',flush=True)
    try:server.serve_forever(poll_interval=.25)
    finally:server.server_close();v.vosk_model_free(model)

if __name__=='__main__':main()
