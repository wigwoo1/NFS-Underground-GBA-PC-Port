from pathlib import Path
import struct,subprocess,json
p=Path('work/camera');out=Path('outputs/nfsug-native-renderer/camera-research')
b=(p/'prototype-runs/threaded-923c5fa0b0c14d9292907cbf8e50cc13-native-scene.bin').read_bytes()
_,offset,size=struct.unpack_from('<III',b,44);w=b[offset:offset+size];magic,count=struct.unpack_from('<II',w);assert magic==0x31444652
position=8;surfaces=[]
for i in range(count):
 n,width,height=struct.unpack_from('<III',w,position);position+=12+n*40
 rgba=w[position:position+width*height*4];position+=len(rgba)
 surfaces.append((width,height,rgba))
assert struct.unpack_from('<II',w,position)==(0x3149574e,count);position+=8
results=[]
for i,(width,height,rgba) in enumerate(surfaces):
 mode,length=struct.unpack_from('<II',w,position);position+=8;states=w[position:position+length];position+=length
 if i not in (10,25):continue
 assert mode==2 and length==width*height
 path=p/f'captured-wall-gpu-{i}.bin';path.write_bytes(struct.pack('<III',width,height,2)+rgba+states)
 run=subprocess.run([str((p/'captured-wall-gpu-preview.exe').resolve()),str(path.resolve())],capture_output=True,text=True,timeout=30)
 results.append(dict(surface=i,returncode=run.returncode,output=run.stdout.strip(),stderr=run.stderr.strip()))
 assert run.returncode==0,results[-1]
assert len(results)==2
report=dict(result='PASS',materials=results,full_4k_pixels_checked=16588800,scope='Actual captured arc/chevron GPU textures, nearest sampling, two U repeats, and zero-writer discard over flat full4K quad. Exact-boundary pixels permit only the adjacent nearest texel and are counted separately. Does not verify world perspective or original column addressing.')
(out/'captured-wall-gpu-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
