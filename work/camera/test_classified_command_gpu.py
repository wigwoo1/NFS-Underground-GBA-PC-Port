from pathlib import Path
import subprocess,json,sys
p=Path('work/camera').resolve()
python=sys.executable;alpha=sys.argv[1] if len(sys.argv)>1 else '0.5'
result=subprocess.run([python,str(p/'test_classified_command_scene.py'),alpha],capture_output=True,text=True);assert result.returncode==0,(result.stdout,result.stderr)
images=[]
for name in ('indexed','classified'):
 prefix=p/f'{name}-command-gpu'
 run=subprocess.run([str(p/'zero-snapshot-preview.exe'),str(p/f'{name}-command-scene.packet'),str(prefix),str(p/'zero-gpu-rows.bin')],capture_output=True,text=True)
 assert run.returncode==0,(name,run.returncode,run.stdout,run.stderr)
 images.append(Path(str(prefix)+'.rgba').read_bytes())
assert len(images[0])==len(images[1])==3840*2160*4
changed=sum(images[0][i:i+4]!=images[1][i:i+4] for i in range(0,len(images[0]),4))
assert changed>0,'Affine mapping correction must affect this mixed-mode scene'
scene=json.loads((p/'classified-command-scene-tests.json').read_text())
report=dict(result='PASS',sample_alpha=float(alpha),rendered_rgba_pixels=3840*2160,changed_pixels_from_legacy_perspective=changed,captured_commands=scene['captured_commands'],walls=scene['walls'],lit_walls=scene['lit_walls'],scope='Mixed affine/perspective scene endpoint GPU smoke test. Difference from legacy perspective is expected, not evidence of original pixel parity. Original span fidelity and live timing remain unverified.')
(p/f'classified-command-gpu-{alpha}-tests.json').write_text(json.dumps(report,indent=2));
(p/'classified-command-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
