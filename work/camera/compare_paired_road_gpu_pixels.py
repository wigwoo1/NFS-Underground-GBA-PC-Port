from pathlib import Path
import ctypes as C,json,struct,subprocess
p=Path('work/camera');roads=json.loads((p/'world-source-clipped-rings.json').read_text())['checks'];native=C.CDLL(str((p/'road-pair-samples.dll').resolve())).nf_road_pair_samples;native.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());reports=[]
for road in roads:
 samples=(C.c_int32*(38400*4))();assert native((C.c_double*(len(road['clipped_ring'])*6))(*(v for row in road['clipped_ring'] for v in row)),len(road['clipped_ring']),(C.c_uint16*4)(*road['bounds']),table,samples)
 old=(p/f"stable-road-{road['command']}-gpu-input.bin").read_bytes();_,oldn,w,h=struct.unpack_from('<4I',old);texture=old[16+oldn*40+4:];assert len(texture)==w*h
 input=p/f"paired-road-{road['command']}-gpu-input.bin";output=p/f"paired-road-{road['command']}-gpu-output.rgba";input.write_bytes(struct.pack('<6I',0x32504752,38400,w,h,int(road['normalization'][0]*2),int(road['normalization'][1]*2))+bytes(samples)+texture)
 run=subprocess.run([str((p/'road-pair-gpu-probe.exe').resolve()),str(input),str(output)],capture_output=True,text=True,timeout=60);assert run.returncode==0,run.stdout+run.stderr;pixels=output.read_bytes();assert len(pixels)==3840*2160*4
 expected=(p/f"stable-road-{road['command']}-all-original-samples.bin").read_bytes();targets={};generated={}
 for i in range(0,len(expected),5):dest,index=struct.unpack_from('<IB',expected,i);targets[dest]=index
 for y in range(160):
  for x in range(240):
   at=((2159-int((y+.5)*13.5))*3840+300+int((x+.5)*13.5))*4
   if pixels[at+3]:generated[y*240+x]=pixels[at]
 overlap=targets.keys()&generated.keys();reports.append(dict(command=road['command'],targets=len(targets),gpu_pixels=len(generated),missing=len(targets.keys()-generated.keys()),extra=len(generated.keys()-targets.keys()),overlap=len(overlap),index_mismatches=sum(targets[k]!=generated[k] for k in overlap)))
report=dict(result='PASS',checks=reports,scope='Actual GPU paired-coordinate texture addressing endpoint diagnostic. Cell quads deliberately reproduce original coverage; not continuous native4K coverage or motion/fullscene proof.')
(p/'paired-road-gpu-pixel-comparison.json').write_text(json.dumps(report,indent=2));print(report)

assert all(c['missing']==c['extra']==c['index_mismatches']==0 for c in reports)
