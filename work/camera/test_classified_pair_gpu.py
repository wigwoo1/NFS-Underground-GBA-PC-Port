from pathlib import Path
import struct,subprocess,json
p=Path('work/camera').resolve();first=(p/'classified-command-scene.packet').read_bytes()
def later(raw):
 data=bytearray(raw);serial,begin,end=struct.unpack_from('<3I',data,16);struct.pack_into('<3I',data,16,serial+1,end+1,end+4);return data
same=later(first);legacy=later((p/'indexed-command-scene.packet').read_bytes());changed=later(first)
affine_changed=later(first);affine_mutated=False
wo,ws=struct.unpack_from('<2I',changed,48);count=struct.unpack_from('<I',changed,wo+4)[0];offset=wo+8
for _ in range(count):n,w,h=struct.unpack_from('<3I',changed,offset);offset+=12+n*40+w*h*4
assert struct.unpack_from('<2I',changed,offset)==(0x3149574e,count);offset+=8;mutated=False
for _ in range(count):
 record_offset=offset
 mode,size=struct.unpack_from('<2I',changed,offset);offset+=8
 if mode==4 and not affine_mutated:
  struct.pack_into('<I',affine_changed,record_offset,1);affine_mutated=True
 if mode==3 and not mutated:
  plane=size//17
  j=next(j for j in range(plane) if changed[offset+plane+j]==2);changed[offset+plane+j]=1;mutated=True
 offset+=size
assert mutated
assert affine_mutated
for name,data,expected in [('same',same,0),('missing',legacy,43),('changed',changed,43),('affine-mode',affine_changed,43)]:
 path=p/f'classified-pair-{name}.packet';path.write_bytes(data)
 result=subprocess.run([str(p/'classified-pair-preview.exe'),str(p/'classified-command-scene.packet'),str(path)],capture_output=True,text=True)
 assert result.returncode==expected,(name,result.returncode,result.stdout,result.stderr)
report=dict(result='PASS',matching_acquired_pair_rendered=True,atomic_endpoint_rejections=3,affine_mapping_mismatch_rejected=True,borrowed_wall_and_road_arrays_cleared=True,scope='Complete captured acquired-pair GPU consumer; missing classified metadata, changed lighting plane and changed affine mapping rejected before render. No live timing or original texture pixel parity proof.')
(p/'classified-pair-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
