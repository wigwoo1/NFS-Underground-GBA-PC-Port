"""Reject invalid capture windows through the actual diagnostic host startup."""
from pathlib import Path
import json, os, subprocess

p = Path('work/camera').resolve()
rom = 'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
command = [str(p/'native-endpoint-road-attributes.exe'), str(p/'visibility-probe-wide.dll'), rom,
           str(p.parent/'driving.state'), str(p/'capture-window-rejected.csv'),
           '--paired-packets', '--layer-sync', '--scripted-route', '--seconds', '1',
           '--delay-refreshes', '8', '--window-buffer']
cases = []
for value in ['', '-1', '216001', '180junk', '4294967296']:
    env = {k: v for k, v in os.environ.items() if not k.startswith('NF_CAPTURE_')}
    env['NF_CAPTURE_START_FRAME'] = value
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
    cases.append(dict(value=value, exit_code=result.returncode))
    assert result.returncode == 17, (cases[-1], result.stdout, result.stderr)
report = dict(result='PASS', cases=cases,
              scope='Actual diagnostic host rejects malformed/out-of-range windows before simulation; valid default and later windows verified separately by complete frame captures.')
(p/'capture-window-tests.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
