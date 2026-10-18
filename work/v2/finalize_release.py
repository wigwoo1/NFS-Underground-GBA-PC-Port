from pathlib import Path
import zipfile,hashlib,json,shutil
from PIL import Image
out=Path('outputs/nfsug-native-renderer');src=Path('work/v2/package/NFSUG-Native-Renderer-source')
assert Path('work/v2/packaged.ppm').read_bytes()==Path('work/v2/release.ppm').read_bytes()
shutil.copy2('work/v2/boot-test.json',out/'boot-test.json')
for n in ['scene-tests.json','host-test.json','cpu-cadence.json','physics-observations.json']:shutil.copy2(out/n,src/'tests'/n)
shutil.copy2('work/v2/test_scene.py',src/'tests/test_scene_local.py')
# Preserve the exact local reproduction scripts as records, noting their local fixture requirements.
(src/'tests/README.md').write_text('Controller tests run from Build.ps1. test_scene_local.py records the local comparison experiment and requires the original work/race.state fixture and local bridge DLL paths; it is not a portable test runner. JSON files record observed results and scope. Game snapshots and ROM data are not bundled.\n')
with zipfile.ZipFile(out/'NFSUG-Native-Renderer-source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in src.rglob('*'):
  if p.is_file() and not any(x in ('build','deps') for x in p.relative_to(src).parts):z.write(p,p.relative_to(src.parent))
result={'clean_source_build':'PASS','controller_mapping_cases':21,'packaged_framebuffer_matches_development_build':True,'executable_sha256':hashlib.sha256((out/'NFSUG-Native-Renderer.exe').read_bytes()).hexdigest(),'source_archive_sha256':hashlib.sha256((out/'NFSUG-Native-Renderer-source.zip').read_bytes()).hexdigest()}
(out/'release-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
Image.open('work/v2/boot.ppm').resize((960,540)).save('work/v2/boot-preview.png')
