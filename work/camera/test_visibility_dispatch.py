from pathlib import Path
import re,json
p=Path('work/camera');s=(p/'live_visibility.h').read_text();required=set(re.findall(r'pc\s*[!=]=\s*(0x[0-9a-fA-F]+)',s));dispatch=set(re.findall(r'case (0x[0-9a-fA-F]+):',s));assert required==dispatch,(required-dispatch,dispatch-required)
report=dict(result='PASS',event_addresses=len(required),scope='Static dispatch coverage for literal pc equality/inequality event checks; new dynamic/range checks require review.')
(p/'visibility-dispatch-tests.json').write_text(json.dumps(report,indent=2));print(report)
