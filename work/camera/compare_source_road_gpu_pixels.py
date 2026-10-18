from pathlib import Path
import ctypes as C,json,struct,subprocess
p=Path('work/camera');roads=json.loads((p/'world-source-clipped-rings.json').read_text())['checks'];tri=C.CDLL(str((p/'source-road-triangulate.dll').resolve())).nf_source_triangles;tri.argtypes=[C.c_void_p,C.c_uint,C.c_void_p];reports=[]
for road in roads:
 points=[[v[0],v[1],16777216/v[3],v[4]/(v[3]*road['normalization'][0]),v[5]/(v[3]*road['normalization'][1])] for v in road['clipped_ring']];ring=(C.c_double*(len(points)*5))(*(v for row in points for v in row));out=(C.c_double*(192*5))();n=tri(ring,len(points),out);assert n
 old=(p/f"stable-road-{road['command']}-gpu-input.bin").read_bytes();_,oldn,w,h=struct.unpack_from('<4I',old);texture=old[16+oldn*40+4:];assert len(texture)==w*h
 input=p/f"source-road-{road['command']}-gpu-input.bin";output=p/f"source-road-{road['command']}-gpu-output.rgba";input.write_bytes(struct.pack('<4I',0x31504752,n,w,h)+bytes(out)[:n*40]+struct.pack('<I',0)+texture)
 run=subprocess.run([str((p/'road-index-gpu-probe.exe').resolve()),str(input),str(output)],capture_output=True,text=True,timeout=60);assert run.returncode==0,run.stdout+run.stderr;pixels=output.read_bytes();assert len(pixels)==3840*2160*4
 expected=(p/f"stable-road-{road['command']}-all-original-samples.bin").read_bytes();targets={};generated={}
 for i in range(0,len(expected),5):dest,index=struct.unpack_from('<IB',expected,i);targets[dest]=index
 for y in range(160):
  for x in range(240):
   at=((2159-int((y+.5)*13.5))*3840+300+int((x+.5)*13.5))*4
   if pixels[at+3]:generated[y*240+x]=pixels[at]
 overlap=targets.keys()&generated.keys();reports.append(dict(command=road['command'],targets=len(targets),gpu_pixels=len(generated),missing=len(targets.keys()-generated.keys()),extra=len(generated.keys()-targets.keys()),overlap=len(overlap),index_mismatches=sum(targets[k]!=generated[k] for k in overlap)))
report=dict(result='MEASURED',checks=reports,scope='Actual4K fixedfunction GPU, source world-derived clipped rings; triangle raster coverage and ideal perspective texture interpolation compared to original paired writer. Not final sampler/fullscene proof.')
(p/'source-road-gpu-pixel-comparison.json').write_text(json.dumps(report,indent=2));print(report)
