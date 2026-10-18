from pathlib import Path
import ctypes as C,json,struct,subprocess
p=Path('work/camera');fn=C.CDLL(str((p/'road-pair-samples.dll').resolve())).nf_road_pair_samples;fn.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring'];out=(C.c_int32*(38400*4))();assert fn((C.c_double*(len(ring)*6))(*(v for row in ring for v in row)),len(ring),(C.c_uint16*4)(*road['bounds']),table,out)
 shader=p/f"road-{road['command']}-coverage.frag";shader.write_text((p/'road_source_coverage_uv_execute.frag').read_text().replace('while(scan<=160)',f"while(scan<={road['bounds'][3]})"));rf=p/f"road-{road['command']}-span-gpu-ring.bin"
 for begin in [0,12800,25600]:
  records=[struct.pack('<10i',i,*([0]*7),out[i*4+2] if out[i*4]>=0 else -77,out[i*4+3] if out[i*4]>=0 else -77) for i in range(begin,begin+12800)];cases=p/f"road-{road['command']}-coverage-{begin}.bin";cases.write_bytes(struct.pack('<I',12800)+b''.join(records));run=subprocess.run([str((p/'road-source-span-probe.exe').resolve()),str(shader),str(cases),str(p/'road-correction-reciprocal.bin'),str(rf)],capture_output=True,text=True,timeout=60);assert run.returncode==0,run.stdout;checks.append(dict(command=road['command'],begin=begin,cases=12800,output=run.stdout))
report=dict(result='PASS',checks=checks,scope='Actual GPU complete destination->source mapping->span->pairedUV from native geometry. Entire38400 outputs perroad compared; integer endpoint only, no native4K motion/live timing proof.');(p/'road-source-coverage-uv-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
