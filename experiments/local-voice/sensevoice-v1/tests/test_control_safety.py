#!/usr/bin/env python3
"""Guardrail tests: no network requests or real HA control are performed."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

p=Path(__file__).resolve().parents[1]/'server.py'
spec=importlib.util.spec_from_file_location('zuk_voice_control_safety',p)
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

# Mock registry/mapping; all entity IDs are synthetic.
v.registry_entities=lambda:[{'entity_id':'light.example_living_room','domain':'light','name':'test light','area':'test'}]
v.mapping_get=lambda:{'客厅灯':'light.example_living_room'}
v.read_token=lambda:'test-only-token-not-sent'
calls=[]
def fake_ha_call(method, path, token, payload=None):
    calls.append((method,path,token,payload))
    return 200
v.ha_call=fake_ha_call

p=v.add_pending_confirmation(v.preview('打开客厅灯'))
assert p['understood'] and p['confirmation_required'] and p['confirm_id']
assert v.claim_pending_confirmation('invalid') is None
# A fresh plan is required after invalid nonce.
p=v.add_pending_confirmation(v.preview('打开客厅灯'))
assert v.claim_pending_confirmation(p['confirm_id'])==('light.example_living_room','turn_on')
assert v.claim_pending_confirmation(p['confirm_id']) is None

p=v.add_pending_confirmation(v.preview('打开客厅灯'))
res,status=v.execute_confirmed_light(p['confirm_id'])
assert status==200 and res['submitted'] and res['action']=='turn_on'
assert calls==[('POST','/api/services/light/turn_on','test-only-token-not-sent',{'entity_id':'light.example_living_room'})],calls
res,status=v.execute_confirmed_light(p['confirm_id'])
assert status==409 and len(calls)==1

p=v.add_pending_confirmation(v.preview('关闭客厅灯'))
res,status=v.execute_confirmed_light(p['confirm_id'])
assert status==200 and calls[-1][1]=='/api/services/light/turn_off'

# Can't control cover/climate or unmapped devices.
for utterance in ['关闭窗帘','把空调调到26度','打开卧室灯','打开灯']:
    plan=v.add_pending_confirmation(v.preview(utterance))
    assert 'confirm_id' not in plan,(utterance,plan)

# Token required to make any real HA call.
p=v.add_pending_confirmation(v.preview('打开客厅灯'))
v.read_token=lambda:''
before=len(calls)
res,status=v.execute_confirmed_light(p['confirm_id'])
assert status==412 and len(calls)==before

# Saving a token goes only to an isolated file, using 0600, after mocked HA check.
with TemporaryDirectory() as d:
    v.TOKEN_FILE=Path(d)/'ha-token.private'
    assert not v.token_available()
    try:
        v.store_token('short')
    except ValueError:
        pass
    else:raise AssertionError('short token was accepted')
    v.store_token('synthetic_validity_test_token_123456789')
    assert v.TOKEN_FILE.read_text()=='synthetic_validity_test_token_123456789'
    assert v.TOKEN_FILE.stat().st_mode & 0o777 == 0o600

print('CONTROL_SAFETY_TESTS_OK one_time_confirmations token_gate fixed_light_domain no_real_HA_calls')
