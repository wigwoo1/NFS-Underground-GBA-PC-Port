"""Stage exact original-wall scene fixtures without replacing earlier diagnostic inputs."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys
base=Path(r'C:\NFSUG-Workspace');old=base/'NFSUG-restored-composition-gpu-fixtures';exact=base/'NFSUG-wall-assets-fixtures';out=base/'NFSUG-wall-retention-gpu-fixtures';out.mkdir(exist_ok=True);here=Path(__file__).resolve().parent
for p in old.iterdir():
 if p.is_file():shutil.copyfile(p,out/p.name)
for p in exact.iterdir():
 if p.is_file() and (p.suffix in ('.nrb','.nrp','.nfre','.bin','.nwh','.ref') or p.name=='source-fixture-capture-report.json'):shutil.copyfile(p,out/p.name)
matched=0
for p in exact.glob('road-*.nfre'):
 assert p.read_bytes()==(old/p.name).read_bytes(),p.name
 matched+=1
for script in ('run_road_retention_host.py','run_wall_retention_host.py','prepare_restored_background_references.py'):subprocess.run([sys.executable,str(here/script),'--folder',str(out)],check=True)
report=dict(result='PASS_EXACT_WALL_COMPOSITION_STAGING',road_assets_unchanged=matched,road_history_sha256=hashlib.sha256((out/'original-road-events.nrj').read_bytes()).hexdigest(),wall_history_sha256=hashlib.sha256((out/'original-wall-history.nwh').read_bytes()).hexdigest(),original_fixtures_preserved=True)
(out/'wall-stage-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
