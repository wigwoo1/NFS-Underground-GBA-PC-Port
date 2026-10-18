from pathlib import Path
import json,hashlib,sys
sys.path.insert(0,r'C:\NFSUG-Workspace\NFSUG-tools\python-libs')
import capstone
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-rotation-trace-v2-core')
d=json.loads((out/'probe/rotation-events.json').read_text());rs=d['records'];assert d['header'][10]==1
previous=next(r for r in rs if r[2]==847 and r[3]==4)
current=next(r for r in rs if r[2]==848 and r[3]==4)
entry=next(r for r in rs if r[2]==848 and r[3]==1)
assert previous[110:119]!=current[110:119] and current[110:122]==entry[84:96]
assert current[110:122]!=entry[96:108] and current[29]==0x0200c24c and entry[6]==0x0200c27c
code=(out/'probe/first-failure-iwram.bin').read_bytes();md=Cs(CS_ARCH_ARM,CS_MODE_ARM)
instructions=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str,bytes=i.bytes.hex()) for i in md.disasm(code[0x25f0:0x2604],0x030025f0)]
assert [(x['mnemonic'],x['operands']) for x in instructions]==[('ldrb','r2, [r7, #0x88]'),('ldr','r3, [r6, #0xfc]'),('add','r2, r2, r2, lsl #1'),('add','r3, r3, r2, lsl #4'),('str','r3, [sp, #0x84]')]
report=dict(result='PASS_TRAFFIC_SLOT_CHANGED_BEFORE_CAPTURED_PRODUCER',scene=848,previous_scene=847,required_slot=hex(current[29]),other_slot=hex(entry[6]),requested_matrix_current=current[110:122],requested_matrix_previous=previous[110:122],matrix_already_changed_before_observed_producer=True,previous_matrix_reuse_ruled_out=True,slot_formula='word(state+0xfc) + byte(object+0x88)*48',slot_selection_instructions=instructions,capstone_version=capstone.__version__,limitations='Does not yet identify every writer or reconstruct the missing world rotation. Output matrix includes camera composition; do not use it as the independent object rotation.',evidence_sha256={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [out/'probe/rotation-events.json',out/'probe/first-failure-iwram.bin',out/'rotation-trace-v2-core-test-report.json']},full_scene_60fps=False)
(out/'traffic-slot-evidence.json').write_text(json.dumps(report,indent=2));print(report['result'])
