#!/usr/bin/env python3
"""Unit tests: no HA access required and absolutely no service calls."""
import importlib.util
from pathlib import Path
P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('voicev1', P/'server.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
expect={
    '打开客厅灯': ('客厅灯','turn_on'),
    '关闭客厅灯': ('客厅灯','turn_off'),
    '打开主卧灯': ('主卧灯','turn_on'),
    '关闭主卧窗帘': ('主卧窗帘','turn_off'),
    '把客厅空调调到二十六度': ('客厅空调','set_temperature'),
    '客厅空调设置为26度': ('客厅空调','set_temperature'),
}
for utterance,(alias,act) in expect.items():
    p=v.parse_intent(utterance)
    assert p.get('valid') and p['alias']==alias and p['action']==act,(utterance,p)
assert v.parse_intent('把客厅空调调到二十六度')['temperature']==26
for s in ('打开灯','打开卧室的窗户','关卧室灯并且打开卧室灯','把客厅空调调到60度','打开阳台灯'):
    assert not v.parse_intent(s)['valid'],(s,v.parse_intent(s))
assert v.preview('打开客厅灯')['executed'] is False
assert not v.preview('打开灯')['understood']
print('PREVIEW_TESTS_OK',len(expect)+5,'no_actuation')
