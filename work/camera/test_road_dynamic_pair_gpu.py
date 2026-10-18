from pathlib import Path
import ctypes as C,json,struct,subprocess
p=Path('work/camera');fn=C.CDLL(str((p/'road-pair-samples.dll').resolve())).nf_road_pair_samples;fn.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring'];out=(C.c_int32*(38400*4))();assert fn((C.c_double*(len(ring)*6))(*(v for row in ring for v in row)),len(ring),(C.c_uint16*4)(*road['bounds']),table,out);records=[]
 for i in range(38400):
  row,x,u,v=out[i*4:i*4+4]
  if row>=0:records.append(struct.pack('<10i',row,x,*([0]*6),u,v))
 cases=p/f"road-{road['command']}-dynamic-pair-cases.bin";cases.write_bytes(struct.pack('<I',len(records))+b''.join(records));rf=p/f"road-{road['command']}-span-gpu-ring.bin";rf.write_bytes(struct.pack('<I',len(ring))+b''.join(struct.pack('<8d',r[0],r[1],r[3],r[4],r[5],0,0,0) for r in ring));run=subprocess.run([str((p/'road-source-span-probe.exe').resolve()),str(p/'road_source_dynamic_pair_execute.frag'),str(cases),str(p/'road-correction-reciprocal.bin'),str(rf)],capture_output=True,text=True,timeout=60);assert run.returncode==0,run.stdout;checks.append(dict(command=road['command'],native_source_coordinate_cases=len(records),output=run.stdout))
report=dict(result='PASS',checks=checks,scope='Actual GPU source spans derive padded pair width and position; native C ledger supplies row/X including duplicated/spilled writes. Integer endpoint UV parity only, coverage scheduler stillCPU, not continuous4K/live gameplay.');(p/'road-dynamic-pair-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
