from pathlib import Path
p=Path('work/camera');s=(p/'test_segmented_original_gpu_parity.py').read_text()
s=s.replace("owned-gpu-segmented-source-candidate.dll","owned-sky-source-context-4k-candidate.dll").replace("owned-sky-hud-view-candidate.dll","owned-sky-source-context-candidate.dll")
a=s.index('  import struct,gc\n');b=s.index(' assert len(set(images))>1',a)
s=s[:a]+'''  owned=OwnedSourceDraw(bytes(frame),camera,models,bounds,detail['geometry_records'],*source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
  assert gpu.nf_owned_gpu_source_context_callback(C.byref(owned.context))==0
  assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==before,'4K window candidate full-scene mismatch'
  checks.append(dict(alpha=alpha,sha256=digest))
'''+s[b:]
s=s.replace("PASS_SEGMENTED_COMPLETE_SOURCE_4K_PIXELS","PASS_4K_WINDOW_COMPLETE_SOURCE_PIXELS")
a=s.index("scope=str(len(checks))+");b=s.index('\nPath(sys.argv[2])',a)
s=s[:a]+"scope='Complete captured scene fractional4KRGB exact versus existing playable source-context GPU. Separate closed contexts; diagnostic readbacks, not live cadence/scanout proof.')"+s[b:]
(p/'test_source_context_4k_fullscene.py').write_text(s)
