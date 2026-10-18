"""Export exact sampled native RGBA sources; never declare a finished texture pack."""
from pathlib import Path
import hashlib,importlib.util,io,json,struct
from PIL import Image
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port')
audit_path=root/'outputs/nfsug-native-renderer/camera-research/texture-compatibility-20261017/compatibility-report.json'
audit=json.loads(audit_path.read_text());assert audit['result']=='VERIFIED_SAMPLED_TEXTURE_COMPATIBILITY_AUDIT'
refs=Path(r'C:\NFSUG-Workspace\NFSUG-pc-scene-tests/references')
dest=root/'outputs/nfsug-native-renderer/texture-sources/current-native-sample-20261017';sources=dest/'source';sources.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('native_source_hash',root/'work/v2/texture_hash.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
expected={(r['width'],r['height'],r['upload_rgba_sha256']):r for r in audit['variants'] if not r['indexed']}
entries={};written=0
for scene in audit['scenes']:
 path=refs/scene['name'];assert sha(path)==scene['sha256'];stream=io.BytesIO(path.read_bytes())
 def read(n):
  b=stream.read(n);assert len(b)==n;return b
 def integer():return struct.unpack('>I',read(4))[0]
 def buffer():return read(integer())
 epoch,refresh,owners,split,count=struct.unpack('>2Q3I',read(28));buffer();buffer()
 for command in range(count):
  info=struct.unpack('>16Q',read(128));buffer();buffer();images=[buffer() for _ in range(integer())]
  for _ in range(integer()):read(integer()*4)
  if info[6]:continue
  w,h=info[3:5]
  for level,rgba in enumerate(images):
   assert len(rgba)==w*h*4
   digest=hashlib.sha256(rgba).hexdigest();key=(w,h,digest);entry=expected[key];identity=f'{module.source_hash(rgba,w,h):016x}';assert identity==entry['source_key']
   if identity not in entries:
    png=sources/(identity+'.png')
    if not png.exists():Image.frombytes('RGBA',(w,h),rgba).save(png)
    with Image.open(png) as image:assert image.size==(w,h) and image.convert('RGBA').tobytes()==rgba
    written+=png.stat().st_size;assert written<=16*1024*1024,'Unexpectedly large source export'
    entries[identity]=dict(source='source/'+png.name,width=w,height=h,source_hash=identity,rgba_sha256=digest,png_sha256=sha(png),model=entry['model'],wall=entry['wall'],uses=[])
   entries[identity]['uses'].append(dict(scene=scene['name'],epoch=epoch,refresh=refresh,owner=info[0],command=command,original_command_index=info[15],material_index=info[2],lighting_level=level,lit=bool(info[8])))
 assert not stream.read()
assert len(entries)==len(expected)==54
inventory=dict(format='NFSUG-NATIVE-TEXTURE-SOURCE-INVENTORY-1',result='VERIFIED_EXACT_NATIVE_RGBA_SOURCE_EXPORT',complete=False,regenerated=False,source_count=len(entries),source_png_bytes=written,source_png_rgba_roundtrip_exact=True,source_ids_match_native_uploads=True,ready_marker_created=False,scenes=audit['scenes'],sources=list(entries.values()),excluded_indexed_variants=[r for r in audit['variants'] if r['indexed']],audit_sha256=sha(audit_path),runner_sha256=sha(Path(__file__)),
    limits='Original-resolution decoded upload sources from nine frozen scenes. Shading/alpha are part of exact source identity. No upscaling, AI regeneration, live selection, full-game coverage or performance claim. Indexed variants are metadata only; their per-row historical palette cannot be replaced by treating index bytes as colors.')
(dest/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf8')
assert not (dest/'pack.ready').exists() and not (dest/'textures/4k/pack.ready').exists()
print(json.dumps({k:v for k,v in inventory.items() if k not in ['sources','scenes','excluded_indexed_variants']},indent=2))
