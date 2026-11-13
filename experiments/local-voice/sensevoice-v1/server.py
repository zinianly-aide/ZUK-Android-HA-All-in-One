#!/usr/bin/env python3
"""ZUK SenseVoice V1.1: offline ASR + HA mapping + manual light control.

Only verified light entities or the Xiaomi 86v1 ceiling-light relay may be controlled,
with a fresh one-time manual confirmation. No arbitrary switch control.
No automatic actions. A user-created HA token stays in a private on-device file.
"""
import ctypes
import json
import os
import re
import secrets
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from pathlib import Path
from threading import Lock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
WEB = ROOT / 'web'
MODEL = ROOT / 'model' / 'model.int8.onnx'
TOKENS = ROOT / 'model' / 'tokens.txt'
LIB = ROOT / 'lib' / 'libzuk-sensevoice.so'
STORAGE = Path('/data/data/com.termux/files/home/zuk-ha-native/config-ha/.storage')
MAPPING = ROOT / 'mapping.private.json'
TOKEN_FILE = ROOT / 'ha-token.private'
HA_BASE = 'http://127.0.0.1:8125'
CONFIRM_LOCK = Lock()
PENDING = {'value': None}
CONFIRM_TTL = 30
MAX_PCM = 16000 * 2 * 9
LOCK = Lock()
ALIASES = {
    '客厅灯': 'switch', '主卧灯': 'light', '卧室灯': 'light',
    '次卧灯': 'light', '书房灯': 'light', '餐厅灯': 'light',
    '客厅窗帘': 'cover', '主卧窗帘': 'cover', '卧室窗帘': 'cover',
    '客厅空调': 'climate', '主卧空调': 'climate', '卧室空调': 'climate',
}
ROOMS = ['客厅', '主卧', '次卧', '卧室', '书房', '餐厅', '阳台', '厨房']
CATEGORIES = ['灯', '窗帘', '空调']
ALLOWED_DOMAINS = {'light', 'cover', 'climate', 'switch'}
# Fixed MIOT service/property of the middle relay (吸顶灯) in Xiaomi Smart Home Panel.
# Other switch relays and household plugs are NEVER exposed for voice control.
PANEL_MODEL = 'xiaomi.controller.86v1'
PANEL_CEILING_RELAY_SUFFIX = '_86v1_on_p_11_1'


def compact(s):
    return re.sub(r'[\s，。,.!?！？：:、；;]+', '', str(s or '')).lower()


def chinese_number(s):
    digits = {'零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
              '六': 6, '七': 7, '八': 8, '九': 9}
    if s.isdigit():
        return int(s)
    if s in digits:
        return digits[s]
    if s.startswith('十'):
        return 10 + (digits.get(s[1:], 0) if len(s) > 1 else 0)
    if '十' in s:
        a, b = s.split('十', 1)
        if a in digits and (not b or b in digits):
            return digits[a] * 10 + digits.get(b, 0)
    return None


def parse_intent(transcript):
    s = compact(transcript)
    if not s:
        return {'valid': False, 'reason': '没有识别到内容'}
    # Explicit multi-room phrases are not single-target commands.
    # Explicitly mentioned room names must be unique, including 主卧 vs 卧室.
    found_rooms = {r for r in ROOMS if r in s}
    if len(found_rooms) > 1:
        return {'valid': False, 'reason': '同时提到了多个房间，请一次只控制一个设备'}
    room = next(iter(found_rooms), None)
    category = next((c for c in CATEGORIES if c in s), None)
    if not category:
        return {'valid': False, 'reason': '未明确说出灯、窗帘或空调'}
    # "卧室" might match both main and guest bedroom: never auto infer.
    if not room:
        return {'valid': False, 'reason': '请明确说出房间名称'}
    alias = room + category
    # These are different circuits or fixtures, even if their names contain '灯'.
    # With the panel's three relays, never interpret '灯带/风扇灯' as '客厅灯'.
    if alias == '客厅灯' and any(x in s for x in (
        '灯带', '风扇灯', '筒灯', '射灯', '氛围灯', '台灯',
        '壁灯', '落地灯', '夜灯', '灯条', '灯管')):
        return {'valid': False, 'reason': '你说的是其他灯具，不是面板第二路吸顶灯'}
    if alias not in ALIASES:
        return {'valid': False, 'reason': '这个房间设备尚不在 V1 白名单'}
    domain = ALIASES[alias]
    if domain == 'climate':
        m = re.search(r'(?:调到|设置为?|设为?|调成)(\d{1,2}|[零一二两三四五六七八九十]{1,4})度', s)
        if m:
            n = chinese_number(m.group(1))
            if n is None or n < 16 or n > 30:
                return {'valid': False, 'reason': '温度超出实验允许范围（16–30℃）'}
            return {'valid': True, 'alias': alias, 'domain': domain,
                    'action': 'set_temperature', 'temperature': n}
    off = any(x in s for x in ('关闭', '关上', '关掉', '关灯', '关一下', '合上'))
    off = off or s.startswith('关')
    on = any(x in s for x in ('打开', '开启', '开灯', '开一下', '升起'))
    if on == off:
        return {'valid': False, 'reason': '动作不明确或指令互相冲突'}
    return {'valid': True, 'alias': alias, 'domain': domain,
            'action': 'turn_on' if on else 'turn_off'}


def read_json(path):
    try:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def registry_entities():
    reg = read_json(STORAGE / 'core.entity_registry').get('data', {}).get('entities', [])
    devs = read_json(STORAGE / 'core.device_registry').get('data', {}).get('devices', [])
    areas = read_json(STORAGE / 'core.area_registry').get('data', {}).get('areas', [])
    by_device = {d.get('id'): d for d in devs}
    by_area = {a.get('id'): a.get('name', '') for a in areas}
    result = []
    for e in reg:
        eid = e.get('entity_id', '')
        domain = eid.split('.', 1)[0]
        if domain not in ALLOWED_DOMAINS or e.get('disabled_by'):
            continue
        dev = by_device.get(e.get('device_id'), {})
        area = by_area.get(e.get('area_id') or dev.get('area_id'), '')
        name = e.get('name') or e.get('original_name') or dev.get('name_by_user') or dev.get('name') or eid
        if domain == 'switch':
            # Only this exact MIOT second-channel relay of the Xiaomi panel.
            if not (dev.get('model') == PANEL_MODEL and
                    eid.endswith(PANEL_CEILING_RELAY_SUFFIX) and
                    '吸顶灯' in str(name) and area == '客厅'):
                continue
        result.append({'entity_id': eid, 'domain': domain, 'name': str(name)[:90],
                       'area': str(area)[:70], 'panel_model': dev.get('model') if domain == 'switch' else None})
    result.sort(key=lambda x: (x['domain'], x['area'], x['name']))
    return result



def safe_voice_target(alias, entity):
    """Allow a mapped lamp or exactly the Xiaomi ceiling-light relay, never a plug."""
    if not isinstance(entity, dict) or alias not in ALIASES:
        return False
    if entity.get('domain') != ALIASES[alias]:
        return False
    if entity.get('domain') == 'light':
        return True
    return (alias == '客厅灯' and entity.get('domain') == 'switch'
            and entity.get('panel_model') == PANEL_MODEL
            and str(entity.get('entity_id', '')).endswith(PANEL_CEILING_RELAY_SUFFIX)
            and '吸顶灯' in str(entity.get('name', ''))
            and entity.get('area') == '客厅')


def mapping_get():
    loaded = read_json(MAPPING)
    return loaded if isinstance(loaded, dict) else {}


def preview(text):
    p = parse_intent(text)
    if not p['valid']:
        return {'understood': False, 'reason': p['reason'], 'executed': False}
    mapping = mapping_get()
    eid = mapping.get(p['alias'])
    row = next((x for x in registry_entities() if x['entity_id'] == eid
                and safe_voice_target(p['alias'], x)), None)
    out = {'understood': True, 'alias': p['alias'], 'action': p['action'],
           'temperature': p.get('temperature'), 'mapping_status': 'verified' if row else 'unmapped',
           'entity': row, 'executed': False}
    if not row:
        out['reason'] = '请先在下方为此语音名称选择真实 HA 实体'
    return out



def token_available():
    return TOKEN_FILE.is_file() and TOKEN_FILE.stat().st_size > 20


def read_token():
    try:
        return TOKEN_FILE.read_text(encoding='utf-8').strip()
    except OSError:
        return ''


def ha_call(method, path, token, payload=None):
    """Local HA only, hardcoded safe paths; never record credentials in logs."""
    if not token or not path.startswith('/api/'):
        raise ValueError('invalid HA request')
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    req = Request(HA_BASE + path, data=data, method=method,
                  headers={'Authorization': 'Bearer ' + token,
                           'Content-Type': 'application/json'})
    with urlopen(req, timeout=8) as response:
        # HA service response can be an array; status code is enough for dispatch.
        response.read(4096)
        return response.status


def panel_ceiling_state():
    """Read-only view of current Xiaomi panel middle relay (no write action)."""
    eid = mapping_get().get('客厅灯')
    row = next((x for x in registry_entities() if x['entity_id'] == eid
                and safe_voice_target('客厅灯', x)), None)
    if row is None:
        return {'mapped': False, 'available': False}, 200
    token = read_token()
    if not token:
        return {'mapped': True, 'available': False, 'reason': 'token_not_configured'}, 200
    req = Request(HA_BASE + '/api/states/' + eid,
                  headers={'Authorization': 'Bearer ' + token})
    try:
        with urlopen(req, timeout=5) as response:
            state = json.load(response).get('state')
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as e:
        print('PANEL_STATE_READ_ERROR', type(e).__name__, flush=True)
        return {'mapped': True, 'available': False, 'reason': 'ha_state_unavailable'}, 200
    # Only whitelist the expected simple state values, not HA attributes/token.
    return {'mapped': True, 'available': state in ('on', 'off'),
            'state': state if state in ('on', 'off', 'unavailable', 'unknown') else 'unknown',
            'label': '小米智能家庭面板 / 第二路吸顶灯'}, 200


def store_token(value):
    """Validate a user-created token; atomically save locally with 0600 mode."""
    if not isinstance(value, str) or not 25 <= len(value.strip()) <= 2048:
        raise ValueError('invalid_token_length')
    value = value.strip()
    if any(c.isspace() for c in value):
        raise ValueError('invalid_token_format')
    status = ha_call('GET', '/api/', value)
    if status != 200:
        raise ValueError('HA_token_not_accepted')
    tmp = TOKEN_FILE.with_name('ha-token.private.tmp')
    fd = os.open(str(tmp), os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(value)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, TOKEN_FILE)
    finally:
        if tmp.exists():
            tmp.unlink()


def add_pending_confirmation(plan):
    """Issue a one-time capability, never automatically call HA."""
    global PENDING
    with CONFIRM_LOCK:
        PENDING['value'] = None  # supersede any previous utterance
        e = plan.get('entity') or {}
        if not (plan.get('understood') and plan.get('mapping_status') == 'verified'
                and plan.get('action') in ('turn_on', 'turn_off')
                and safe_voice_target(plan.get('alias'), e)):
            return plan
        nonce = secrets.token_urlsafe(32)
        PENDING['value'] = (nonce, time.monotonic(), plan['alias'],
                            e['entity_id'], plan['action'])
        plan['confirmation_required'] = True
        plan['confirm_id'] = nonce
        plan['expires_in_seconds'] = CONFIRM_TTL
        return plan


def claim_pending_confirmation(nonce):
    """Single use; validate latest private mapping again immediately before use."""
    if not isinstance(nonce, str):
        return None
    with CONFIRM_LOCK:
        item = PENDING.get('value')
        PENDING['value'] = None
    if not item or not secrets.compare_digest(item[0], nonce):
        return None
    _, created, alias, eid, action = item
    if time.monotonic() - created > CONFIRM_TTL:
        return None
    if ALIASES.get(alias) not in ('light', 'switch') or action not in ('turn_on', 'turn_off'):
        return None
    if mapping_get().get(alias) != eid:
        return None
    if not any(row['entity_id'] == eid and safe_voice_target(alias, row)
               for row in registry_entities()):
        return None
    return eid, action, ALIASES[alias]


def execute_confirmed_light(nonce):
    """Manual-only HA action for a validated light OR the exact Xiaomi panel relay."""
    token = read_token()
    if not token:
        return {'error': 'ha_token_not_configured'}, 412
    item = claim_pending_confirmation(nonce)
    if item is None:
        return {'error': 'no_fresh_matching_confirmation'}, 409
    eid, action, domain = item
    if domain not in ('light', 'switch'):
        return {'error': 'unsupported_control_domain'}, 400
    try:
        status = ha_call('POST', '/api/services/' + domain + '/' + action, token,
                         {'entity_id': eid})
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as e:
        print('HA_SAFE_SWITCH_DISPATCH_ERROR', type(e).__name__, flush=True)
        return {'error': 'ha_request_failed_or_token_expired'}, 502
    return {'submitted': status == 200, 'action': action,
            'entity_id': eid, 'domain': domain, 'ha_http_status': status,
            'note': 'HA API accepted request; verify device state separately'}, 200


class Engine:
    def __init__(self):
        v = ctypes.CDLL(str(LIB))
        v.zuk_sensevoice_init.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        v.zuk_sensevoice_init.restype = ctypes.c_int
        v.zuk_sensevoice_recognize_pcm16.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
        v.zuk_sensevoice_recognize_pcm16.restype = ctypes.c_int
        self.v = v
        t0 = time.monotonic()
        rc = v.zuk_sensevoice_init(os.fsencode(MODEL), os.fsencode(TOKENS), 2)
        if rc != 0:
            raise RuntimeError('offline model could not be initialized')
        print('SENSEVOICE_LOADED_SEC', round(time.monotonic() - t0, 3), flush=True)

    def transcribe(self, pcm):
        b = ctypes.create_string_buffer(pcm)
        o = ctypes.create_string_buffer(4096)
        with LOCK:
            t0 = time.monotonic()
            n = self.v.zuk_sensevoice_recognize_pcm16(b, len(pcm) // 2, o, len(o))
            dt = round((time.monotonic() - t0) * 1000)
        if n < 0:
            raise RuntimeError('offline inference error')
        return o.value.decode('utf-8', errors='replace'), dt


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # No transcript, PCM, entity names, account data or query args logged.
        print('REQ', self.command, self.path.split('?', 1)[0], flush=True)

    def respond(self, data, code=200, mime='application/json; charset=utf-8'):
        raw = (data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(raw)

    def allowed(self):
        return self.headers.get('Host', '') in ('127.0.0.1:8127', 'localhost:8127')

    def safe_post(self):
        return self.headers.get('Origin', '') in ('http://127.0.0.1:8127', 'http://localhost:8127')

    def do_GET(self):
        if not self.allowed():
            return self.respond({'error': 'loopback_only'}, 403)
        p = self.path.split('?', 1)[0]
        if p == '/health':
            return self.respond({'ready': True, 'engine': 'SenseVoice INT8', 'offline': True,
                                 'ha_connected': STORAGE.exists(), 'token_configured': token_available(),
                                 'actions_enabled': token_available(), 'manual_confirmation_only': True,
                                 'model_preloaded': True})
        if p == '/panel-ceiling-state':
            body, status = panel_ceiling_state()
            return self.respond(body, status)
        if p == '/entities':
            return self.respond({'entities': registry_entities(), 'aliases': ALIASES,
                                 'mapping': mapping_get(), 'actions_enabled': token_available(),
                                 'manual_confirmation_only': True})
        if p in ('/', '/index.html'):
            return self.respond((WEB / 'index.html').read_text(encoding='utf-8'), mime='text/html; charset=utf-8')
        if p == '/app.js':
            return self.respond((WEB / 'app.js').read_text(encoding='utf-8'), mime='application/javascript; charset=utf-8')
        return self.respond({'error': 'not_found'}, 404)

    def do_POST(self):
        if not self.allowed() or not self.safe_post():
            return self.respond({'error': 'same_origin_only'}, 403)
        p = self.path.split('?', 1)[0]
        try:
            n = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.respond({'error': 'bad_length'}, 400)
        if p == '/recognize':
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/octet-stream':
                return self.respond({'error': 'bad_content_type'}, 415)
            if n < 3200 or n > MAX_PCM or n % 2:
                return self.respond({'error': 'audio_size_invalid'}, 400)
            pcm = self.rfile.read(n)
            if len(pcm) != n:
                return self.respond({'error': 'incomplete_audio'}, 400)
            try:
                text, ms = self.server.engine.transcribe(pcm)
            except Exception as e:
                print('INFERENCE_ERROR', type(e).__name__, flush=True)
                return self.respond({'error': 'inference_failed'}, 500)
            planned = add_pending_confirmation(preview(text))
            return self.respond({'text': text, 'elapsed_ms': ms,
                                 'plan': planned, 'offline': True, 'executed': False})
        if p == '/map':
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json' or not 2 <= n <= 512:
                return self.respond({'error': 'invalid_mapping_body'}, 400)
            try:
                req = json.loads(self.rfile.read(n))
                alias, eid = req['alias'], req['entity_id']
            except (ValueError, TypeError, KeyError):
                return self.respond({'error': 'invalid_json'}, 400)
            if alias not in ALIASES or not isinstance(eid, str):
                return self.respond({'error': 'unsupported_alias'}, 400)
            row = next((e for e in registry_entities() if e['entity_id'] == eid
                        and safe_voice_target(alias, e)), None)
            if not row:
                return self.respond({'error': 'entity_not_found_or_wrong_domain'}, 400)
            # Writes ONLY explicit alias/entity_id pairs; never writes to HA .storage.
            with LOCK:
                mapping = mapping_get()
                mapping[alias] = eid
                tmp = MAPPING.with_suffix('.tmp')
                tmp.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
                os.chmod(tmp, 0o600)
                os.replace(tmp, MAPPING)
            with CONFIRM_LOCK:
                PENDING['value'] = None  # mapping change invalidates older confirmation
            return self.respond({'saved': True, 'alias': alias, 'entity': row,
                                 'actions_enabled': token_available()})
        if p == '/credentials':
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json' or not 2 <= n <= 2300:
                return self.respond({'error': 'invalid_token_body'}, 400)
            try:
                req = json.loads(self.rfile.read(n))
                store_token(req['token'])
            except (HTTPError, URLError, TimeoutError, ValueError, OSError, KeyError, TypeError) as e:
                print('HA_TOKEN_SETUP_FAILED', type(e).__name__, flush=True)
                return self.respond({'error': 'HA_token_validation_failed'}, 400)
            return self.respond({'configured': True, 'manual_confirmation_only': True})
        if p == '/confirm':
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json' or not 2 <= n <= 200:
                return self.respond({'error': 'invalid_confirmation_body'}, 400)
            try:
                req = json.loads(self.rfile.read(n))
            except (TypeError, ValueError):
                return self.respond({'error': 'invalid_json'}, 400)
            answer, code = execute_confirmed_light(req.get('confirm_id'))
            return self.respond(answer, code)
        return self.respond({'error': 'not_found'}, 404)


def main():
    print('SENSEVOICE_V1_INITIALIZING manual-confirm-only listen=127.0.0.1:8127', flush=True)
    engine = Engine()
    server = ThreadingHTTPServer(('127.0.0.1', 8127), Handler)
    server.engine = engine
    print('SENSEVOICE_V1_READY offline=true manual-confirm-only', flush=True)
    server.serve_forever(poll_interval=0.3)


if __name__ == '__main__':
    main()
