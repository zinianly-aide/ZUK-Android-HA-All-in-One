#!/data/data/com.termux/files/usr/bin/bash
P=/data/data/com.termux/files/usr
H=/data/data/com.termux/files/home
LAB="$H/zuk-ha-native"; CFG="$LAB/config-ha"; V="$LAB/venv-ha"
export PREFIX="$P" HOME="$H" PATH="$P/bin:/system/bin" TMPDIR="$P/tmp"
export LD_LIBRARY_PATH="$P/lib" LD_PRELOAD="$P/lib/libc++_ha_termux30.so"
exec > "$LAB/logs/xiaomi-official-verification.log" 2>&1
"$V/bin/python" - <<'PY'
import importlib,sys,pathlib,json,traceback
cfg=pathlib.Path('/data/data/com.termux/files/home/zuk-ha-native/config-ha')
sys.path.insert(0,str(cfg))
modules=['construct','paho.mqtt.client','numpy','psutil','cryptography','custom_components.xiaomi_home','custom_components.xiaomi_home.miot.miot_mips','custom_components.xiaomi_home.miot.miot_cloud','custom_components.xiaomi_home.config_flow']
failures=0
for mod in modules:
 try:
  m=importlib.import_module(mod)
  print('XIAOMI_IMPORT_OK',mod,getattr(m,'__file__',''),flush=True)
 except Exception as ex:
  print('XIAOMI_IMPORT_FAIL',mod,type(ex).__name__,str(ex),flush=True)
  traceback.print_exc(limit=9)
  failures+=1
m=json.loads((cfg/'custom_components/xiaomi_home/manifest.json').read_text())
print('OFFICIAL_COMPONENT_VERSION',m['domain'],m['version'],'failures',failures,flush=True)
raise SystemExit(bool(failures))
PY
RC=$?
echo "XIAOMI_IMPORT_TEST_RC=$RC $(date)"
exit "$RC"
