from pathlib import Path
import ctypes as C,struct,json,math,subprocess
p=Path('work/camera');fn=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve())).nf_road_pair_uv_continuous;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());data=(p/'road-pair-uv-gpu-cases.bin').read_bytes();cursor=0;reports=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 command=road['command'];count=len((p/f'stable-road-{command}-all-original-samples.bin').read_bytes())//5;fixture=(p/f'stable-road-{command}-gpu-input.bin').read_bytes();_,_,w,h=struct.unpack_from('<4I',fixture);nu,nv=road['normalization'];records=[];fractions=[]
 for local in range(count):
  i=cursor+local;r=list(struct.unpack_from('<10i',data,4+i*40));f=[((i*13+k*7)%16)/16 for k in range(8)]
  if r[7]==r[3]-1:f[7]=f[6]/2
  out=(C.c_double*2)();assert fn((C.c_double*3)(*(r[k]+f[k] for k in range(3))),(C.c_double*3)(*(r[4+k]+f[3+k] for k in range(3))),r[3]+f[6],r[7]+f[7],table,out)
  r[8:]=[(2*math.floor(out[0]/(65536*nu)*(w/2))+local%2)%w,math.floor(out[1]/(65536*nv)*h)%h];records.append(struct.pack('<10i',*r));fractions.append(struct.pack('<8f',*f))
 cases=p/f'road-{command}-fractional-texel-cases.bin';cases.write_bytes(struct.pack('<I',count)+b''.join(records)+b''.join(fractions));shader=(p/'road_pair_uv_varying_execute.frag').read_text().replace('resultUV=ivec2(roundEven(result));',f'int tx=int(2*floor(result.x/{65536*nu:.1f}*{w/2:.1f}))+index%2,ty=int(floor(result.y/{65536*nv:.1f}*{h}.0));\n resultUV=ivec2((tx%{w}+{w})%{w},(ty%{h}+{h})%{h});');path=p/f'road-{command}-fractional-texel.frag';path.write_text(shader)
 run=subprocess.run([str((p/'road-shader-varying-probe.exe').resolve()),str(path),str(cases),str(p/'road-correction-reciprocal.bin')],capture_output=True,text=True,timeout=60);assert run.returncode==0,run.stdout+run.stderr;assert f'GPU_cases={count} UV_mismatches=0' in run.stdout;reports.append(dict(command=command,cases=count,texture_dimensions=[w,h],normalization=[nu,nv],texel_address_mismatches=0,gpu_output=run.stdout));cursor+=count
report=dict(result='PASS',checks=reports,scope='Actual GPU fractional texel addresses with original road material dimensions/normalization; texture contents, continuous coverage and gameplay remain unverified.');(p/'road-fractional-texel-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
