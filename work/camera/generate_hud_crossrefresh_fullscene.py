from pathlib import Path
p=Path('work/camera');s=(p/'test_source_context_4k_fullscene.py').read_text().replace('owned-sky-source-context-4k-candidate.dll','owned-gpu-segmented-4k-hud-reuse-candidate.dll')
a="  checks.append(dict(alpha=alpha,sha256=digest))"
b='''  import struct
  changed=bytearray(bytes(frame));old_refresh,gn,hn=struct.unpack_from('<3I',changed,4);assert hn==34944*160
  new_refresh=old_refresh+1;struct.pack_into('<I',changed,4,new_refresh);struct.pack_into('<Q',changed,32,new_refresh*280896)
  for y in range(160):struct.pack_into('<I',changed,40+gn+y*34944,new_refresh)
  stats=(C.c_uint64*2)();assert gpu.nf_hud_visual_cache_stats(stats);hits=stats[0]
  cross=OwnedSourceDraw(bytes(changed),camera,models,bounds,detail['geometry_records'],*source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  assert gpu.nf_owned_gpu_source_context_callback(C.byref(cross.context))==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==before,'Refresh-only sky/HUD frame changed pixels'
  assert gpu.nf_hud_visual_cache_stats(stats) and stats[0]==hits+1,'Crossrefresh cache branch not exercised'
  checks.append(dict(alpha=alpha,sha256=digest,synthetic_cross_refresh=[old_refresh,new_refresh],cache_hit=True))'''
assert s.count(a)==1;s=s.replace(a,b).replace('owned-sky-source-context-candidate.dll','owned-sky-hud-view-candidate.dll').replace("Complete captured scene fractional4KRGB exact versus existing playable source-context GPU. Separate closed contexts; diagnostic readbacks, not live cadence/scanout proof.","Captured fullscene fractional4K plus controlled refresh-only identity changes, actual new cache hits pixel-exact. Synthetic identity changes are not real consecutive captured scenes; no live timing/scanout proof.")
(p/'test_hud_crossrefresh_fullscene.py').write_text(s)

