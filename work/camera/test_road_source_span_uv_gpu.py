from pathlib import Path
import ctypes as C,json,struct,subprocess
p=Path('work/camera');fn=C.CDLL(str((p/'road-span-uv-at.dll').resolve())).nf_road_span_uv_at;fn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for row in ring for v in row));records=[]
 for i in range(641):
  out=(C.c_double*4)();ok=fn(data,len(ring),i/4,64.25,20.5,table,out);expected=[round(out[2]),round(out[3])] if ok else [-77,-77];records.append(struct.pack('<10i',*([0]*8),*expected))
 cases=p/f"road-{road['command']}-span-gpu-cases.bin";cases.write_bytes(struct.pack('<I',641)+b''.join(records));rf=p/f"road-{road['command']}-span-gpu-ring.bin";rf.write_bytes(struct.pack('<I',len(ring))+b''.join(struct.pack('<8d',r[0],r[1],r[3],r[4],r[5],0,0,0) for r in ring));run=subprocess.run([str((p/'road-source-span-probe.exe').resolve()),str(p/'road_source_span_uv_execute.frag'),str(cases),str(p/'road-correction-reciprocal.bin'),str(rf)],capture_output=True,text=True,timeout=60);assert run.returncode==0,run.stdout;checks.append(dict(command=road['command'],cases=641,output=run.stdout))
report=dict(result='PASS',checks=checks,scope='Combined actual GPU source-ring span to fractionalUV at quarter rows; explicit fixed width64.25/pair20.5, rounded UV comparison only, not full4K coverage or gameplay.');(p/'road-source-span-uv-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
