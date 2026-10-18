from pathlib import Path
import ctypes as C,json,struct,subprocess,re
p=Path('work/camera');fn=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;fn.argtypes=[C.c_void_p]*5;table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 cmd=road['command'];ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for row in ring for v in row));bounds=(C.c_uint16*4)(*road['bounds']);out=(C.c_int16*(38400*2))();assert fn(data,len(ring),bounds,table,out)
 output=p/f'road-{cmd}-coverage-cache-output.bin';run=subprocess.run([str((p/'road-source-coverage-cache-probe.exe').resolve()),str(p/f'road-{cmd}-coverage-cache.frag'),str(p/f'road-{cmd}-index-cases-0.bin'),str(p/'road-correction-reciprocal.bin'),str(p/f'road-{cmd}-span-gpu-ring.bin'),str(p/f'road-{cmd}-index-texture.bin'),str(output),str(p/'road_source_span_cache.frag')],capture_output=True,text=True,timeout=120);assert run.returncode==0,(run.returncode,run.stdout,run.stderr)
 actual=list(struct.iter_unpack('<2i',output.read_bytes()));assert len(actual)==38400
 for i,pair in enumerate(actual):assert pair==(out[i*2],out[i*2+1]),(cmd,i,pair,tuple(out[i*2:i*2+2]))
 checks.append(dict(command=cmd,exact_destinations=38400,draw_finish_ms=[float(v) for v in re.findall(r'draw_finish_ms=([0-9.]+)',run.stdout)]))
report=dict(result='PASS',checks=checks,scope='GPU span->coverage cache matches native C source-write ledger including empty destinations and source row/X. Integer endpoint diagnostic only; final4K cache consumption pending.');(p/'road-source-coverage-cache-tests.json').write_text(json.dumps(report,indent=2));print(report)
