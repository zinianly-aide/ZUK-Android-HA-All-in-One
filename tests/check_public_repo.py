#!/usr/bin/env python3
"""Static checks for intentionally-public project sources (no secret values)."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
# Validate only paths staged/tracked by Git; ignored local model binaries are not published.
paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).split(b'\0')
tracked = [ROOT / raw.decode('utf-8') for raw in paths if raw]

assert (ROOT / 'README.md').exists()
assert len(list((ROOT / 'docs').glob('*.md'))) >= 9
for p in tracked:
    if p.suffix.lower() in {'.apk', '.aab', '.apks', '.bin', '.db', '.sqlite', '.tar', '.zip', '.whl', '.so', '.key'}:
        raise SystemExit(f'Forbidden binary/secret file: {p.relative_to(ROOT)}')
    if p.stat().st_size > 500_000:
        raise SystemExit(f'Oversized file: {p.relative_to(ROOT)}')
    if p.suffix in {'.md', '.sh', '.py', '.yaml', '.yml', '.example'} or p.name in {'README.md', '10-start-zuk-ha-core'}:
        s = p.read_text(encoding='utf-8')
        if re.search(r'\b192\.168\.\d{1,3}\.\d{1,3}\b|\b[A-Za-z0-9._%+-]+@(?:gmail|qq|outlook|163)\.com\b', s, re.I):
            raise SystemExit(f'Private home/device metadata detected: {p.relative_to(ROOT)}')
        if re.search(r'X-Amz-(?:Signature|Credential|Algorithm|Date)=', s, re.I):
            raise SystemExit(f'Presigned download URL detected: {p.relative_to(ROOT)}')
        if re.search(r'(?i)(?:access_token|refresh_token|client_secret)\s*[:=]\s*["\']?[A-Za-z0-9_-]{20,}', s):
            raise SystemExit(f'Credential-looking value detected: {p.relative_to(ROOT)}')
print(f'OK: checked {len(tracked)} public files')
