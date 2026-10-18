"""Decode scene17 abort from valid builder RAM, never uninitialized comparison fields."""
from pathlib import Path
import json,struct,hashlib
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Native-Current-20261017';folder=out/'lifecycle-gap-results';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((folder/'lifecycle-gap-report.json').read_text());raw=(folder/'visibility-comparison.bin').read_bytes();h=struct.unpack_from('<32Q',raw)
assert h[0]==0x3143504e and h[1]==1 and h[2]==len(raw) and h[4:8]==(2,17,11918,0) and h[19]==2 and h[22:24]==(1,0) and h[24:26]==(20,320)
assert h[16]==1 and h[17]==3 and h[18]==0x48000
query=raw[256+2*h[3]:256+2*h[3]+h[18]];builder=raw[256+2*h[3]+h[18]:256+2*h[3]+2*h[18]]
def offset(address,size):
 if 0x02000000<=address and address+size<=0x02040000:return address-0x02000000
 assert 0x03000000<=address and address+size<=0x03008000;return 0x40000+address-0x03000000
at=offset(h[20],256);state=builder[at:at+256];count=struct.unpack_from('<H',state,238)[0];assert count==23
events=r['step82']['capture_context']['events'];assert len(events)==8 and r['step82']['capture_context']['overflow']==0
aborts=[x for x in events if x[0]==3 and x[2]==0x03004d50];assert len(aborts)==1 and aborts[0][8]==2
line=aborts[0][1];header=out/'lifecycle-native/source/camera/live_visibility.h';branch=header.read_text().splitlines()[line-1];assert 'if(!ok||memcmp(&native,&original,sizeof(native)))' in branch
assert events[-1][8]==0 and r['paired_original_pixels_pcm_clocks_exact']
names=['kind','source_line','guest_pc','refresh','epoch','scene_serial','capture_epoch','capture_serial','capture_stage','pending_snapshot','prepared_mode','pending_models','pending_model_failed','capture_failures','query_refresh','builder_refresh']
report=dict(result='VERIFIED_SCENE17_QUERY_EVALUATION_ABORT_WITH23_ENTRIES_CAPACITY20',expected_original_queue_count=count,configured_capacity=20,evaluator_succeeded=False,original_result_reads_attempted=False,comparison_struct_payload_valid=False,state_address=hex(h[20]),epoch=h[4],scene=h[5],refresh=h[6],abort_guest_pc='0x03004d50',abort_staged_source_line=line,abort_branch=branch,events=[dict(zip(names,x)) for x in events],builder_ram_sha256=hashlib.sha256(builder).hexdigest(),query_ram_sha256=hashlib.sha256(query).hexdigest(),comparison_blob_sha256=sha(folder/'visibility-comparison.bin'),diagnostic_report_sha256=sha(folder/'lifecycle-gap-report.json'),script_sha256=sha(Path(__file__)),next_dependency='Reuse existing supported64-entry configuration, then verify exact early component/clock/PCM parity and full route before offering a replacement.',no_runtime_guard_relaxed=True)
(folder/'lifecycle-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
