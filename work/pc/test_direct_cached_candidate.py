# Reuse complete fixture/core parity tests with cheap cached query support.
from pathlib import Path
import subprocess,sys
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-direct-cached-tests'
s=(base/'NFSUG-pc-owned-sources-tests/test-owned-sources-expanded.py').read_text()
s=s.replace('NFSUG-pc-owned-sources-tests','NFSUG-pc-direct-cached-tests').replace('owned-sources-build-report.json','direct-cached-build-report.json')
s=s.replace('nf_pc_source_reader_open_owned_sources','nf_pc_source_reader_open_direct_sources')
s=s.replace('PASS_OWNED_SOURCES_FRAME_LIFETIMES','PASS_DIRECT_CACHED_FRAME_LIFETIMES').replace('PASS_OWNED_SOURCES_CORE_PARITY','PASS_DIRECT_CACHED_CORE_PARITY')
s=s.replace('owned_source_copy_bytes_removed_first_captures','reader_scratch_copy_bytes_removed_first_captures')
def replace(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b,1)
replace("if fault['name']==name or raw is None or not dest or n<len(raw):return 0", "if fault['name']==name or raw is None:return 0\n  if not dest:return len(raw)\n  if n<len(raw):return 0")
replace("removed=len(original)+sum(len(raw) for (i,k),raw in expected.items() if k==1);assert oldstats[4]-newstats[4]==removed;bytes_saved+=removed", "removed=oldstats[4];assert newstats[0]==newstats[2]==newstats[4]==0;bytes_saved+=removed")
replace("base/'NFSUG-pc-owned-background-tests/capture-host.dll'","base/'NFSUG-pc-owned-sources-tests/capture-host.dll'")
p=out/'test-direct-cached-expanded.py';p.write_text(s);subprocess.run([sys.executable,str(p)],check=True)
subprocess.run([sys.executable,str(here/'test_direct_cached_protocol.py')],check=True)
