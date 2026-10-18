"""Read-only compatibility audit; creates no textures or replacement-ready marker."""
from pathlib import Path
import collections,hashlib,importlib.util,io,json,struct
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');work=root/'work/v2'
references=Path(r'C:\NFSUG-Workspace\NFSUG-pc-scene-tests')
pack_base=work/'build-check/runtime-texture-mixed-preview-20261012';pack=pack_base/'pack-preview/4k'
dest=root/'outputs/nfsug-native-renderer/camera-research/texture-compatibility-20261017';dest.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('canonical_texture_hash',work/'texture_hash.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
manifest=json.loads((pack_base/'manifest.json').read_text());coverage=json.loads((work/'texture_coverage_audit.json').read_text());generation=json.loads((pack_base/'generation-report.json').read_text())
assert manifest['complete'] is False and coverage['status']=='incomplete'
inventory=set(coverage['source_hashes']);assets={};dimensions=collections.Counter()
for row in manifest['textures']:
 source=(pack_base/row['source']).resolve();source.relative_to(pack_base.resolve())
 from PIL import Image
 with Image.open(source) as image:
  image=image.convert('RGBA');w,h=image.size;key=f'{module.source_hash(image.tobytes(),w,h):016x}'
 path=pack/(key+'.rgba');raw=path.read_bytes();magic,version,rw,rh,identity=struct.unpack_from('<4sIIIQ',raw)
 assert magic==b'NFGX' and version==1 and identity==int(key,16)
 assert w<=rw<=4096 and h<=rh<=4096 and len(raw)==24+rw*rh*4
 assert key==source.stem and key not in assets
 assets[key]=dict(source_width=w,source_height=h,replacement_width=rw,replacement_height=rh,source_png_sha256=sha(source),replacement_sha256=hashlib.sha256(raw).hexdigest())
 dimensions[f'{rw}x{rh}']+=1
assert len(assets)==generation['source_count']==59
receipt=json.loads((references/'scene-report.json').read_text())
assert receipt['all_prepared_commands_buffers_palettes_images_columns_exact'] and receipt['original_pixels_exact']
textures={};scenes=[];command_counts=collections.Counter()
for path in sorted((references/'references').glob('*.scene')):
 assert path.stat().st_size<=128*1024*1024
 stream=io.BytesIO(path.read_bytes())
 def read(n):
  value=stream.read(n);assert len(value)==n,'Short scene reference';return value
 def integer():return struct.unpack('>I',read(4))[0]
 def buffer():
  n=integer();assert n<=64*1024*1024;return read(n)
 epoch,refresh,owners,split,count=struct.unpack('>2Q3I',read(28));background=buffer();palette=buffer();assert len(background)==240*160*4 and len(palette)==256*160*4
 for command in range(count):
  info=struct.unpack('>16Q',read(128));vertices=buffer();planes=buffer();images=[buffer() for _ in range(integer())]
  for _ in range(integer()):width=integer();read(width*4)
  owner,model,index,w,h,vertex_count,indexed,wall,lit=info[:9]
  assert model in [0,1] and indexed in [0,1] and wall in [0,1]
  command_counts['models' if model else 'worlds']+=1
  for level,rgba in enumerate(images):
   assert len(rgba)==w*h*4
   digest=hashlib.sha256(rgba).hexdigest();identity=(w,h,indexed,digest)
   if identity not in textures:
    key=f'{module.source_hash(rgba,w,h):016x}'
    textures[identity]=dict(width=w,height=h,indexed=bool(indexed),source_key=key,upload_rgba_sha256=digest,in_legacy_source_inventory=key in inventory,has_existing_replacement=key in assets,occurrences=0,levels=[],model=bool(model),wall=bool(wall))
   entry=textures[identity];entry['occurrences']+=1
   if level not in entry['levels']:entry['levels'].append(level)
 scenes.append(dict(name=path.name,sha256=sha(path),epoch=epoch,refresh=refresh,owners=owners,commands=count))
 assert not stream.read(),'Unexpected trailing data'
assert len(scenes)==9
rows=list(textures.values());color=[r for r in rows if not r['indexed']];indexed=[r for r in rows if r['indexed']]
report=dict(result='VERIFIED_SAMPLED_TEXTURE_COMPATIBILITY_AUDIT',sampled_scene_count=len(scenes),sampled_commands=dict(command_counts),unique_upload_variants=len(rows),true_color_variants=len(color),indexed_variants=len(indexed),true_color_matches_existing_pack=sum(r['has_existing_replacement'] for r in color),true_color_matches_legacy_inventory=sum(r['in_legacy_source_inventory'] for r in color),indexed_byte_matches_existing_pack=sum(r['has_existing_replacement'] for r in indexed),indexed_hash_matches_are_not_color_compatibility=True,
 existing_pack_assets=len(assets),existing_pack_declared_complete=manifest['complete'],pack_ready_present=(pack/'pack.ready').is_file(),pack_preview_present=(pack/'pack.preview').is_file(),replacement_dimension_counts=dict(dimensions),generation_filter=generation['filter'],complete_regenerated_art=generation['complete_regenerated_art'],legacy_inventory_sources=len(inventory),legacy_inventory_status=coverage['status'],scenes=scenes,variants=rows,assets=assets,
 inputs_sha256={str(p):sha(p) for p in [pack_base/'manifest.json',pack_base/'generation-report.json',work/'texture_coverage_audit.json',work/'texture_hash.py',references/'scene-report.json',root/'work/pc/scene_gpu.c',root/'work/pc/source_scene.h']},runner_sha256=sha(Path(__file__)),renderer_changed=False,menu_option_implemented=False,full_game_coverage=False,full_scene_60fps=False,
 limits='Nine existing frozen diagnostic scenes, not all tracks/cars or a new live route. Indexed uploads encode palette indices; direct replacement by decoded RGBA would change historical palette/lighting semantics. Dimension labels describe assets, not a 4K framebuffer or reviewed full-game 4K artwork. Existing pack is an incomplete 4x filtered preview with one generated facade; it must not be marked ready/full.')
(dest/'compatibility-report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['variants','assets','scenes','inputs_sha256']},indent=2))
