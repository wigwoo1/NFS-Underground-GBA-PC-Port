# Full preview regressions and ABBA timing: background-only versus both owned kinds.
from pathlib import Path
import subprocess,sys
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-owned-sources-tests')
s=(here/'verify_owned_background_host.py').read_text(encoding='utf-8-sig')
s=s.replace('NFSUG-pc-owned-background-tests','NFSUG-pc-owned-sources-tests').replace('owned-background-build-report.json','owned-sources-build-report.json')
s=s.replace('owned-background-profile-report.json','owned-sources-profile-report.json').replace('VERIFIED_OWNED_BACKGROUND_HOST_AND_PAIRED_PROFILE','VERIFIED_OWNED_SOURCES_HOST_AND_PAIRED_PROFILE')
s=s.replace("'--owned-background'","'--owned-geometry'")
def replace(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b,1)
replace('here=Path(__file__).resolve().parent;',f'here=Path({str(here)!r});')
replace("cmd=[str(out/'NFSUG-Source-Native-Preview.exe'),'--rom'","cmd=[str(out/'NFSUG-Source-Native-Preview.exe'),'--owned-background','--rom'")
replace("for name,r in t['cases'].items():assert r['owned_background_capture'] and r['background_allocations']==r['background_releases']==r['background_transfers'],(name,r)","for name,r in t['cases'].items():assert r['owned_background_capture'] and r['owned_geometry_capture'] and r['background_allocations']==r['background_releases']==r['background_transfers'] and r['geometry_allocations']==r['geometry_releases']==r['geometry_transfers'],(name,r)")
replace("assert r['owned_background_capture']==owned and r['background_allocations']==r['background_releases']","assert r['owned_background_capture'] and r['owned_geometry_capture']==owned and r['background_allocations']==r['background_releases'] and r['geometry_allocations']==r['geometry_releases']")
replace("r['background_transfers']==r['published_frames'] and r['background_transferred_bytes']>0","r['geometry_transfers']>=r['published_frames'] and r['geometry_transferred_bytes']>0")
s=s.replace("r['background_transferred_bytes']","r['geometry_transferred_bytes']").replace("owned[0]['background_transferred_bytes']","owned[0]['geometry_transferred_bytes']").replace('transferred_background_bytes=','transferred_geometry_bytes=')
s=s.replace("('owned' if owned else 'copied')","('both-owned' if owned else 'background-only')").replace("order='copied,owned,owned,copied'","order='background-only,both-owned,both-owned,background-only'")
p=out/'verify-owned-sources-host-expanded.py';p.write_text(s);subprocess.run([sys.executable,str(p)],check=True)
