from pathlib import Path
import ctypes as C,random,struct,subprocess,json,math
p=Path('work/camera');fn=C.CDLL(str((p/'road-pair-query-continuous.dll').resolve())).nf_road_pair_query_continuous;fn.argtypes=[C.c_double,C.c_double,C.c_void_p];rng=random.Random(261005);records=[];integer=fractional=invalid=0
values=[]
for width in [1,2,31,32,33,64,129]:
 for relative in range(width*2):values.append((width,relative))
for _ in range(8000):
 width=rng.randrange(1,130)+rng.randrange(16)/16;relative=rng.randrange(int(width*2*65536))/65536;values.append((width,relative))
values.extend([(0,0),(32768,0),(10,-1),(10,20),(1,.5),(1,1.9999847412109375)])
for width,relative in values:
 out=C.c_double(-77);ok=fn(width,relative,C.byref(out));a=math.floor(width);b=math.floor(relative);input=[a,b,round((width-a)*65536),round((relative-b)*65536),0,0,0,0];expected=[round(out.value*65536),1] if ok else [-77,-77];records.append(struct.pack('<10i',*input,*expected));invalid+=not ok;integer+=ok and width==int(width) and relative==int(relative);fractional+=ok and (width!=int(width) or relative!=int(relative))
cases=p/'road-pair-query-gpu-cases.bin';cases.write_bytes(struct.pack('<I',len(records))+b''.join(records));run=subprocess.run([str((p/'road-shader-execute-probe.exe').resolve()),str(p/'road_pair_query_execute.frag'),str(cases),str(p/'road-correction-reciprocal.bin')],capture_output=True,text=True,timeout=90);assert run.returncode==0,(run.returncode,run.stdout,run.stderr)
report=dict(result='PASS',cases=len(records),integer=integer,fractional=fractional,invalid=invalid,output=run.stdout,scope='Actual GPU candidate pair query versus C fixed16 result, terminal and invalid-domain cases included. Component only, not final native coverage/texture lane/rowduplication.');(p/'road-pair-query-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
