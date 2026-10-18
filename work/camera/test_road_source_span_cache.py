from pathlib import Path
import ctypes as C,json,struct,subprocess
p=Path('work/camera');fn=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;fn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 cmd=road['command'];ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for row in ring for v in row));output=p/f'road-{cmd}-span-cache-output.bin'
 run=subprocess.run([str((p/'road-source-span-cache-probe.exe').resolve()),str(p/'road_source_span_cache.frag'),str(p/f'road-{cmd}-span-gpu-cases.bin'),str(p/'road-correction-reciprocal.bin'),str(p/f'road-{cmd}-span-gpu-ring.bin'),str(p/f'road-{cmd}-index-texture.bin'),str(output)],capture_output=True,text=True,timeout=60)
 assert run.returncode==0,(run.returncode,run.stdout,run.stderr)
 actual=list(struct.iter_unpack('<4i',output.read_bytes()));assert len(actual)==322
 for row in range(161):
  out=(C.c_double*8)();ok=fn(data,len(ring),row,table,out)
  for side in range(2):
   expected=tuple(round(out[side*4+k]*(65536 if k==0 else 1)) for k in range(4)) if ok else (-77,)*4
   assert actual[row*2+side]==expected,(cmd,row,side,actual[row*2+side],expected)
 checks.append(dict(command=cmd,rows=161,endpoints=322,output=run.stdout))
report=dict(result='PASS',checks=checks,scope='GPU row prepass readback versus C corrected span: integer rows, fixed16 X and rounded UVQ. Diagnostic only; two-pass renderer and timing remain pending.');(p/'road-source-span-cache-tests.json').write_text(json.dumps(report,indent=2));print(report)
