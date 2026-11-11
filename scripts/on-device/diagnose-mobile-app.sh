#!/data/data/com.termux/files/usr/bin/bash
P=/data/data/com.termux/files/usr; H=/data/data/com.termux/files/home; LAB="$H/zuk-ha-native"
export PREFIX="$P" HOME="$H" PATH="$P/bin:/system/bin" TMPDIR="$P/tmp" LD_LIBRARY_PATH="$P/lib" LD_PRELOAD="$P/lib/libc++_ha_termux30.so"
exec > "$LAB/logs/mobile-app-import-diagnostic.log" 2>&1
"$LAB/venv-ha/bin/python" - <<'PY'
import importlib, importlib.metadata as md,traceback
for pkg in ('PyNaCl','cryptography','openai','colorlog','pillow','PyYAML','aiohttp'):
 try:print('METADATA',pkg,md.version(pkg),flush=True)
 except Exception as exc:print('METADATA_FAIL',pkg,type(exc).__name__,str(exc),flush=True)
for module in ('nacl','nacl.secret','homeassistant.components.cloud','homeassistant.components.mobile_app','homeassistant.components.mobile_app.http_api','homeassistant.components.webhook','homeassistant.components.intent','homeassistant.components.person','homeassistant.components.tag'):
 try: mod=importlib.import_module(module); print('IMPORT_OK',module,getattr(mod,'__file__',''),flush=True)
 except Exception as exc:print('IMPORT_FAIL',module,type(exc).__name__,str(exc),flush=True);traceback.print_exc(limit=6)
PY
