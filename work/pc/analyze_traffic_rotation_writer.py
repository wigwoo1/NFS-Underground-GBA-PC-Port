"""Bind original traffic matrix writers to the failed model's requested slot."""
from pathlib import Path
import hashlib,json,sys,collections
sys.path.insert(0,r'C:\NFSUG-Workspace\NFSUG-tools\python-libs')
import capstone
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_MODE_THUMB
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');root=source.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
assert sha(rom)=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593'
original=json.loads((base/'NFSUG-pc-first-model-failure-core/probe/background-gap-probe-report.json').read_text())
evidence=[]
for version in (2,3):
 out=base/f'NFSUG-pc-rotation-trace-v{version}-core';build=json.loads((out/f'rotation-trace-v{version}-build-report.json').read_text());test=json.loads((out/f'rotation-trace-v{version}-core-test-report.json').read_text());probe=json.loads((out/'probe/background-gap-probe-report.json').read_text())
 assert test['result']==f'PASS_ROTATION_TRACE_V{version}_CORE_PARITY'
 assert build['core_sha256']==test['core_sha256']==probe['core_sha256']==sha(out/'capture-host.dll')
 for n,h in build['maintained_source_sha256'].items():assert sha(source/n)==h,n
 assert build['script_sha256']==sha(source/f'build_rotation_trace_v{version}_core.py')
 assert test['maintained_test_sha256']==sha(source/f'test_rotation_trace_v{version}_core.py')
 assert probe['script_sha256']==sha(source/f'probe_rotation_producers_v{version}.py')
 assert test['all_original_pixels_exact'] and test['all_complete_source_bytes_exact'] and test['transfers_balanced'] and test['no_capture_logic_steps']
 assert probe['game_clocks_exact'] and probe['audio_sha256']==original['audio_sha256'] and probe['audio_frames']==original['audio_frames']
 assert [x['logic_step'] for x in probe['failures']]==list(range(3519,3551))
 trace=json.loads((out/'probe/rotation-events.json').read_text());h=trace['header'];records=trace['records']
 assert h[1]==version and h[3]==len(records) and h[6]==848 and h[8]==0 and h[9]==128 and h[10]==1
 assert h[2]*4==len((out/'probe/rotation-trace.bin').read_bytes())
 evidence.append(dict(version=version,core_sha256=build['core_sha256'],records=len(records),sha256={str(q):sha(q) for q in [out/f'rotation-trace-v{version}-build-report.json',out/f'rotation-trace-v{version}-core-test-report.json',out/'probe/background-gap-probe-report.json',out/'probe/rotation-trace.bin',out/'probe/rotation-events.json',out/'probe/first-failure-iwram.bin']}))
consumer=next(r for r in records if r[2]==848 and r[3]==4);assert consumer[21]==0x02005834 and consumer[29]==0x0200c24c and consumer[122]==1
writes=[r for r in records if r[2]==848 and r[3]==7 and 0x0200c24c<=r[64]<0x0200c27c]
assert len(writes)==12 and all(r[1]==15356 and r[65]==4 for r in writes)
assert collections.Counter(r[0] for r in writes)=={0x03004bb8:3,0x03004bd0:3,0x03004bd8:3,0x08022d4c:1,0x08022d50:1,0x08022d54:1}
assembled=[None]*12
for r in writes:assembled[(r[64]-0x0200c24c)//4]=r[66]
assert assembled==consumer[110:122]
last_old=next(r for r in records if r[2]==847 and r[3]==4)
assert assembled[:9]!=last_old[110:119]
player_entry=next(r for r in records if r[2]==848 and r[3]==1)
assert records.index(writes[-1])<records.index(player_entry)<records.index(consumer)
assert player_entry[6]==0x0200c27c
code=(out/'probe/first-failure-iwram.bin').read_bytes();rb=rom.read_bytes();sections=[]
for a,b,mode in [(0x03004af0,0x03004bf4,CS_MODE_ARM),(0x030025f0,0x03002604,CS_MODE_ARM),(0x0806c0ec,0x0806c108,CS_MODE_THUMB),(0x08022c24,0x08022cfa,CS_MODE_THUMB),(0x08022d04,0x08022d66,CS_MODE_THUMB)]:
 data=code[a-0x03000000:b-0x03000000] if a<0x08000000 else rb[a-0x08000000:b-0x08000000]
 sections.append(dict(begin=hex(a),end=hex(b),instructions=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str,bytes=i.bytes.hex()) for i in Cs(CS_ARCH_ARM,mode).disasm(data,a)]))
flat={int(i['address'],16):i for s in sections for i in s['instructions']}
for pc,target in [(0x08022d38,'#0x806c0ec'),(0x08022d44,'#0x806c0ec')]:assert flat[pc]['mnemonic']=='bl' and flat[pc]['operands']==target
assert flat[0x03004bb8]['operands']=='r4, [sl, r6, lsl #2]'
assert flat[0x030025fc]['operands']=='r3, r3, r2, lsl #4'
disassembly=out/'traffic-producer-disassembly.json';disassembly.write_text(json.dumps(dict(capstone_version=capstone.__version__,rom_sha256=sha(rom),code_sha256=sha(out/'probe/first-failure-iwram.bin'),sections=sections),indent=2))
report=dict(result='PASS_CONFIRMED_TRAFFIC_ROTATION_WRITER',scene=848,failed_object=hex(consumer[21]),requested_slot=hex(consumer[29]),write_refresh=15356,consume_refresh=15359,all_twelve_words_bound_to_original_writes=True,writer_pcs=[hex(pc) for pc in sorted(set(r[0] for r in writes))],missing_matrix_entry='0x03004af0',caller='0x08022c24',caller_matrix_calls=['0x08022d38','0x08022d44'],slot_formula='word(state+0xfc) + byte(object+0x88)*48',previous_transform_reuse_ruled_out=True,other_slot_alias_ruled_out=True,limitations='The confirmed slot contains a camera-composed matrix. Capturing it as an independent object rotation would be wrong. No renderer repair, whole-race fidelity or 60-fps gameplay is claimed.',next_dependency='Capture both inputs of the two confirmed traffic matrix calls, derive and validate independent object rotation in the established pose convention, add a per-slot/per-scene producer path without relaxing ownership, then rerun the full varied route and live gates.',evidence=evidence,disassembly_sha256=sha(disassembly),analyzer_sha256=sha(Path(__file__)),other_analyzer_sha256=sha(source/'analyze_rotation_outputs.py'),game_logic_changed=False,playable_preview_changed=False,full_scene_60fps=False,rough_project_percent=68)
(out/'traffic-writer-milestone-report.json').write_text(json.dumps(report,indent=2));print(report['result'])
