from pathlib import Path
import json,struct,subprocess,re,os
os.environ["NF_ROAD_PROBE_FRAMES"]="120"
p=Path('work/camera');checks=[]
for command in [3,4,7]:
 s=(p/f'road-{command}-three-pass-source-index.frag').read_text().replace('sourceCoordinate(texelFetch(cases,ivec2(0,int(gl_FragCoord.x)),0).x)','sourceCoordinate(int(floor((2160-double(gl_FragCoord.y))/13.5))*240+int(floor((double(gl_FragCoord.x)-300)/13.5)))');s=s.replace('void main(){','void main(){\n if(gl_FragCoord.x<300||gl_FragCoord.x>=3540){resultUV=ivec2(-77);return;}');sf=p/f'road-{command}-three-pass-4k-index.frag';sf.write_text(s);output=p/f'road-{command}-three-pass-4k-index-output.bin';run=subprocess.run([str((p/'road-source-three-pass-cpu-timing-probe.exe').resolve()),str(sf),str(p/f'road-{command}-index-cases-0.bin'),str(p/'road-correction-reciprocal.bin'),str(p/f'road-{command}-span-gpu-ring.bin'),str(p/f'road-{command}-index-texture.bin'),str(output),str(p/'road_source_span_cache.frag'),str(p/f'road-{command}-coverage-cache.frag')],capture_output=True,text=True,timeout=180);assert run.returncode==0,run.stdout+run.stderr;pixels=output.read_bytes();assert len(pixels)==3840*2160*8;original=(p/f'stable-road-{command}-all-original-samples.bin').read_bytes();expected={struct.unpack_from('<IB',original,i)[0]:struct.unpack_from('<IB',original,i)[1] for i in range(0,len(original),5)}
 for y in range(160):
  for x in range(240):
   at=((2159-int((y+.5)*13.5))*3840+300+int((x+.5)*13.5))*8;actual=struct.unpack_from('<2i',pixels,at);want=(expected[y*240+x],1) if y*240+x in expected else (-77,-77);assert actual==want,(command,x,y,actual,want)
 checks.append(dict(command=command,original_grid_samples_exact=38400,draw_finish_ms=[float(v) for v in re.findall(r'draw_finish_ms=([0-9.]+)',run.stdout)],output=run.stdout,cpu_pass_ms=[[float(v) for v in line.split(',')] for line in re.findall(r'cpu_pass_ms=([0-9.,]+)',run.stdout)],gpu_pass_ms=[[float(v) for v in line.split(',')] for line in re.findall(r'gpu_pass_ms=([0-9.,]+)',run.stdout)]))
for check in checks:
 times=check['draw_finish_ms'];assert len(times)==120;warm=sorted(times[10:]);check['warm_summary']=dict(samples=len(warm),median_ms=warm[len(warm)//2],p95_ms=warm[int(.95*(len(warm)-1))],max_ms=max(warm),over_16_667_ms=sum(v>1000/60 for v in warm))
for check in checks:
 stages=check['gpu_pass_ms'];assert len(stages)==120;warm=stages[10:];check['gpu_summary']=[dict(pass_name=name,median_ms=sorted(row[k] for row in warm)[55],max_ms=max(row[k] for row in warm)) for k,name in enumerate(['span','coverage','final'])]
for check in checks:
 stages=check['cpu_pass_ms'];assert len(stages)==120;warm=stages[10:];check['cpu_summary']=[dict(pass_name=name,median_ms=sorted(row[k] for row in warm)[55],max_ms=max(row[k] for row in warm)) for k,name in enumerate(['span_submission','coverage_submission','final_submission','finish_wait'])]
 for wall,stage in zip(check['draw_finish_ms'],stages):assert abs(wall-sum(stage))<.00001 and min(stage)>=0
report=dict(result='PASS'   ,checks=checks,scope='Three-pass GPU span and coverage caches plus 4K framebuffer original-grid endpoint road index diagnostic; draw+finish wall timing includes command submission and first-use costs. Not continuous native4K/fullscene60fps.');(p/'road-source-three-pass-cpu-timing-tests.json').write_text(json.dumps(report,indent=2));print(dict(result=report["result"],checks=[dict(command=c["command"],warm_summary=c["warm_summary"],gpu_summary=c["gpu_summary"],cpu_summary=c["cpu_summary"]) for c in checks]))
