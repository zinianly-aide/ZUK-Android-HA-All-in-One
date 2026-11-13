#!/usr/bin/env python3
"""No real HA network calls. Validate panel channel and switch whitelist."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

p = Path(__file__).resolve().parents[1] / 'server.py'
spec = importlib.util.spec_from_file_location('zuk_voice_safe_panel', p)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

PANEL_ID = 'switch.example_xiaomi_86v1_on_p_11_1'
PANEL = {'entity_id': PANEL_ID, 'domain': 'switch', 'name': '吸顶灯 开关',
         'area': '客厅', 'panel_model': 'xiaomi.controller.86v1'}
LIGHT = {'entity_id': 'light.example_bedroom', 'domain': 'light',
         'name': '灯', 'area': '主卧', 'panel_model': None}

v.registry_entities = lambda: [PANEL, LIGHT]
mapping = {'客厅灯': PANEL_ID, '主卧灯': LIGHT['entity_id']}
v.mapping_get = lambda: mapping
v.read_token = lambda: 'test-only-token-is-never-sent-to-network'
calls = []
def fake_ha_call(method, path, token, payload=None):
    calls.append((method, path, payload))
    return 200
v.ha_call = fake_ha_call

# This exact physical middle channel may be called using unambiguous turn_on/off.
plan = v.preview('打开客厅灯')
assert plan['understood'] and plan['mapping_status'] == 'verified'
assert plan['entity']['entity_id'] == PANEL_ID
p = v.add_pending_confirmation(plan)
assert p.get('confirmation_required') and p.get('confirm_id')
assert not calls   # Recognizing voice must never call HA.
assert v.claim_pending_confirmation('forged') is None

p = v.add_pending_confirmation(v.preview('打开客厅灯'))
nonce = p['confirm_id']
assert v.claim_pending_confirmation(nonce) == (PANEL_ID, 'turn_on', 'switch')
assert v.claim_pending_confirmation(nonce) is None

p = v.add_pending_confirmation(v.preview('打开客厅灯'))
result, status = v.execute_confirmed_light(p['confirm_id'])
assert status == 200 and result['submitted']
assert calls[-1] == ('POST', '/api/services/switch/turn_on', {'entity_id': PANEL_ID})
result, status = v.execute_confirmed_light(p['confirm_id'])
assert status == 409 and len(calls) == 1
p = v.add_pending_confirmation(v.preview('关闭客厅灯'))
result, status = v.execute_confirmed_light(p['confirm_id'])
assert status == 200 and calls[-1] == ('POST','/api/services/switch/turn_off',{'entity_id':PANEL_ID})

# Existing ordinary lamp controls elsewhere are still allowed.
p = v.add_pending_confirmation(v.preview('打开主卧灯'))
assert p.get('confirmation_required')
result, status = v.execute_confirmed_light(p['confirm_id'])
assert status == 200 and calls[-1][1] == '/api/services/light/turn_on'

# Plug, other panel channels, counterfeit panel metadata and wrong room must fail.
invalid = [
  {'entity_id':'switch.plug_relay','domain':'switch','name':'吸顶灯','panel_model':'xiaomi.controller.86v1','area':'客厅'},
  {'entity_id':'switch.example_xiaomi_86v1_on_p_10_1','domain':'switch','name':'吸顶灯','panel_model':'xiaomi.controller.86v1','area':'客厅'},
  {'entity_id':'switch.example_xiaomi_86v1_on_p_12_1','domain':'switch','name':'吸顶灯','panel_model':'xiaomi.controller.86v1','area':'客厅'},
  {'entity_id':PANEL_ID,'domain':'switch','name':'吸顶灯','panel_model':'other.switch','area':'客厅'},
  {'entity_id':PANEL_ID,'domain':'switch','name':'吸顶灯','panel_model':'xiaomi.controller.86v1','area':'卧室'},
  {'entity_id':PANEL_ID,'domain':'switch','name':'风扇灯','panel_model':'xiaomi.controller.86v1','area':'客厅'},
]
for row in invalid:
    assert not v.safe_voice_target('客厅灯',row),row

# An old direct light entity in existing private mapping is now invalid for 客厅灯.
mapping['客厅灯'] = 'light.example_living_room'
assert not v.preview('打开客厅灯')['entity']
mapping['客厅灯'] = PANEL_ID

for utterance in ('关闭窗帘','把空调调到26度','打开卧室灯','打开灯'):
    plan=v.add_pending_confirmation(v.preview(utterance))
    assert 'confirm_id' not in plan,(utterance,plan)

# No token means no appliance access; nonce cannot be used without it.
p=v.add_pending_confirmation(v.preview('打开客厅灯'))
v.read_token=lambda:''
result,status=v.execute_confirmed_light(p['confirm_id'])
assert status==412 and len(calls)==3

with TemporaryDirectory() as d:
    v.TOKEN_FILE=Path(d)/'ha-token.private'
    try:v.store_token('short')
    except ValueError:pass
    else:raise AssertionError('short token accepted')
    v.store_token('synthetic_validity_test_token_123456789')
    assert v.TOKEN_FILE.stat().st_mode & 0o777 == 0o600

print('CONTROL_SAFETY_TESTS_OK panel_second_relay_only fixed_switch_service nonce_one_time no_actual_HA_calls')
