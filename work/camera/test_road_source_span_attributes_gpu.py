from pathlib import Path
import ctypes as C,json,struct,subprocess
p=Path('work/camera');fn=C.CDLL(str((p/'road-span-transition-at.dll').resolve())).nf_road_span_transition_at;fn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for component,name in [(1,'U'),(2,'V'),(3,'Q')]:
 shader=(p/'road_source_span_execute.frag').read_text().replace('dvec2(a.x,b.x)*65536',f'dvec2(a[{component}],b[{component}])');sf=p/f'road_source_span_{name}_execute.frag';sf.write_text(shader)
 for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
  ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for row in ring for v in row));records=[]
  for i in range(641):
   out=(C.c_double*8)();ok=fn(data,len(ring),i/4,table,out);expected=[round(out[component]),round(out[4+component])] if ok else [-77,-77];records.append(struct.pack('<10i',*([0]*8),*expected))
  cases=p/f"road-{road['command']}-span-gpu-cases.bin";cases.write_bytes(struct.pack('<I',641)+b''.join(records));rf=p/f"road-{road['command']}-span-gpu-ring.bin";rf.write_bytes(struct.pack('<I',len(ring))+b''.join(struct.pack('<8d',r[0],r[1],r[3],r[4],r[5],0,0,0) for r in ring));run=subprocess.run([str((p/'road-source-span-probe.exe').resolve()),str(sf),str(cases),str(p/'road-correction-reciprocal.bin'),str(rf)],capture_output=True,text=True,timeout=60);assert run.returncode==0,run.stdout;checks.append(dict(command=road['command'],component=name,cases=641,output=run.stdout))
report=dict(result='PASS',checks=checks,scope='Actual GPU source span U/V/Q at quarter rows, rounded integer units; continuous4K coverage and motion/timing remain unverified.');(p/'road-source-span-attributes-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
