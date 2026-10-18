from pathlib import Path
import subprocess,sys
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-direct-cached-tests'
s=(base/'NFSUG-pc-owned-sources-tests/verify-owned-sources-host-expanded.py').read_text()
s=s.replace('NFSUG-pc-owned-sources-tests','NFSUG-pc-direct-cached-tests').replace('owned-sources-build-report.json','direct-cached-build-report.json').replace('owned-sources-profile-report.json','direct-cached-profile-report.json')
s=s.replace('VERIFIED_OWNED_SOURCES_HOST_AND_PAIRED_PROFILE','VERIFIED_DIRECT_CACHED_HOST_AND_PAIRED_PROFILE')
s=s.replace("'--owned-geometry'","'--direct-cached'").replace("'--owned-background'","'--owned-geometry'")
def replace(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b,1)
replace("assert r['owned_background_capture'] and r['owned_geometry_capture']==owned", "assert r['owned_background_capture'] and r['owned_geometry_capture'] and r['direct_cached_capture']==owned")
s=s.replace("r['geometry_transferred_bytes']","r['cached_final_write_bytes']").replace("owned[0]['geometry_transferred_bytes']","owned[0]['cached_final_write_bytes']").replace('transferred_geometry_bytes=','direct_final_write_bytes=')
s=s.replace("('both-owned' if owned else 'background-only')","('direct-final' if owned else 'scratch-copies')").replace("order='background-only,both-owned,both-owned,background-only'","order='scratch,direct,direct,scratch'")
replace("rom=root.parent/'Need", "for name,r in t['cases'].items():assert r['direct_cached_capture'] and r['reader_scratch_bytes']==r['reader_copied_bytes']==0,(name,r)\nrom=root.parent/'Need")
replace("if owned:assert r['geometry_transfers']>=r['published_frames'] and r['cached_final_write_bytes']>0", "if owned:assert r['geometry_transfers']>=r['published_frames'] and r['cached_final_write_bytes']>0 and r['reader_scratch_bytes']==r['reader_copied_bytes']==0")
replace("assert before=={str(p):sha(p) for p in (rom,state)}", "assert all(r['cached_final_writes']==3*r['geometry_transfers'] for r in owned)\nassert before=={str(p):sha(p) for p in (rom,state)}")
p=out/'verify-direct-cached-host-expanded.py';p.write_text(s);subprocess.run([sys.executable,str(p)],check=True)
