from pathlib import Path
import struct,json,hashlib
p=Path('work/camera');checks=[]
for ordinal in (3,4,7):
 gpu=(p/f'stable-road-{ordinal}-gpu-rgba.bin').read_bytes();assert len(gpu)==3840*2160*4;predictions=(p/f'stable-road-{ordinal}-cpu-samples.bin').read_bytes();assert len(predictions)%6==0
 different=missing=original_difference=0;examples=[]
 for pos in range(0,len(predictions),6):
  dest,cpu,original=struct.unpack_from('<IBB',predictions,pos);x=dest%240;y=dest//240;at=((2159-int((y+.5)*13.5))*3840+300+int((x+.5)*13.5))*4;actual=gpu[at];alpha=gpu[at+3];missing+=alpha!=255;different+=actual!=cpu;original_difference+=actual!=original
  if (actual!=cpu or alpha!=255) and len(examples)<8:examples.append(dict(pixel=[x,y],cpu=cpu,gpu=actual,alpha=alpha))
 checks.append(dict(ordinal=ordinal,samples=len(predictions)//6,cpu_gpu_index_differences=different,gpu_missing_coverage=missing,gpu_original_index_differences=original_difference,examples=examples,readback_sha256=hashlib.sha256(gpu).hexdigest()))
report=dict(result='MEASURED',checks=checks,scope='Actual AMD OpenGL offscreen4K native triangles nearest repeat and projective texture coordinate divide, compared CPU source sampling. Fixed-function texture path diagnostic; production shader equivalence not assumed. Isolated roads; no final overdraw/palette/full-scene fidelity or gameplay timing claim.')
(p/'stable-road-gpu-index-comparison.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
