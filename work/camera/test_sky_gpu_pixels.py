import argparse,json,subprocess,hashlib
from pathlib import Path
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
from owned_sky_color import sky_rgba
p=argparse.ArgumentParser();p.add_argument("--executable",required=True);p.add_argument("--fixture",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--case",choices=["actual","wrap","asset"],default="actual");a=p.parse_args()
a.output.mkdir(exist_ok=True)
fixture=a.fixture
if a.case!="actual":
 from dataclasses import replace
 from owned_sky_scroll import source_offset
 import shutil
 fixture=a.output/"inputs";fixture.mkdir(exist_ok=True)
 for name in ["asset.bin","palettes.bin","pair.bin"]:shutil.copy2(a.fixture/name,fixture/name)
 old=SkyBoundary.decode((a.fixture/"old.nfsk").read_bytes());new=SkyBoundary.decode((a.fixture/"new.nfsk").read_bytes());data=(fixture/"asset.bin").read_bytes()
 if a.case=="wrap":
  pair=[]
  for b,angle in [(old,4090),(new,4104)]:
   offset=source_offset(angle,240,0);pair.append(replace(b,angle=angle,source=b.asset_origin+offset,indices=data[offset:offset+15136]))
  old,new=pair
 else:new=replace(new,asset_origin=new.asset_origin+65536,source=new.source+65536)
 (fixture/"old.nfsk").write_bytes(old.encode());(fixture/"new.nfsk").write_bytes(new.encode())
run=subprocess.run([a.executable,str(fixture),str(a.output)],capture_output=True,text=True)
(a.output/"runtime.txt").write_text(run.stdout+run.stderr)
assert run.returncode==0,run.stdout+run.stderr
old=SkyBoundary.decode((fixture/"old.nfsk").read_bytes());new=SkyBoundary.decode((fixture/"new.nfsk").read_bytes())
asset=SkyAsset(old.asset_origin,(fixture/"asset.bin").read_bytes());palette=(fixture/"palettes.bin").read_bytes()
results=[]
for phase in range(1,8):
 if a.case=="asset":
  from owned_sky_sampler import SkySamples
  sample=SkySamples(old.indices,old.indices,0,old.destination)
 else:sample=asset.sample_continuous(old,new,phase/8)
 rgba=sky_rgba(sample,palette);expected=bytearray(bytes([12,34,56])*38400)
 for i in range(15136):expected[(10560+i)*3:(10560+i+1)*3]=rgba[i*4:i*4+3]
 actual=(a.output/f"phase-{phase}.rgb").read_bytes();assert len(actual)==len(expected)
 differences=[abs(x-y) for x,y in zip(actual,expected)]
 assert max(differences)<=1,(phase,max(differences))
 results.append(dict(alpha=phase/8,max_error=max(differences),pixels=38400,gpu_sha256=hashlib.sha256(actual).hexdigest(),reference_sha256=hashlib.sha256(expected).hexdigest()))
assert a.case=="asset" or len({r["gpu_sha256"] for r in results})>=2,"No visible GPU image change in this moving source fixture"
report=dict(result="PASS",case=a.case,frames=results,source_pixels_checked=7*38400,scope="Actual offscreen GPU sky pixels versus independent original-index/per-scanline-palette reference. Includes unchanged pixels outside the sky copy. Not full-game presentation-rate verification.")
epoch_run=subprocess.run([a.executable,str(fixture),str(a.output),"--stale-epoch"],capture_output=True,text=True)
assert epoch_run.returncode==0 and "stale_epoch=1" in epoch_run.stdout,epoch_run.stdout+epoch_run.stderr
report["stale_epoch_rejected"]=True
(a.output/"verification.json").write_text(json.dumps(report,indent=2));print("PASS GPU sky pixels",7*38400,"source-pixel samples; max RGB error",max(r["max_error"] for r in results))
