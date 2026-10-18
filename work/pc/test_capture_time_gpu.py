from pathlib import Path
import hashlib,json,subprocess,os,shutil,collections
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-pose-capture-timing-tests';previous=base/'NFSUG-pc-owner-pose-draw-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
verified=json.loads((previous/'identity-test-report.json').read_text())['test_sha256'];paths=[p for p in previous.glob('owner-pose-real-*.py') if sha(p)==verified];assert len(paths)==1
text=paths[0].read_text().replace('NFSUG-pc-owner-pose-draw-tests','NFSUG-pc-pose-capture-timing-tests')
build=json.loads((previous/'live-build-report.json').read_text());probe=json.loads((out/'timing-build-report.json').read_text());build.update(core_sha256=probe['core_sha256'],exe_sha256=None,result='REUSED_GPU_DLL_WITH_READONLY_TIMING_CORE_DIAGNOSTIC_ONLY');(out/'live-build-report.json').write_text(json.dumps(build,indent=2));shutil.copyfile(previous/'owner-pose-draw.dll',out/'owner-pose-draw.dll')
marker='pose_results=[];last_sky=None;timing_windows=[]';assert text.count(marker)==1;text=text.replace(marker,marker+"\nowner_times={};pose_time_getter=fn(core,'nf_pc_source_pose_timing',[Q,U,U,U,P,S,P,S])")
marker='last_sky=expected';assert text.count(marker)==1;text=text.replace(marker,marker+'''
 for role in range(fi[4]):
  k=(Q*5)();w=(Q*16)();cam=C.create_string_buffer(56);assert owner(frame,role,k) and pose_time_getter(k[0],k[1],k[2],k[3],w,128,cam,56);owner_times[tuple(k)]=tuple(w)
''')
marker="info=(Q*7)();assert sky_info(pair,info);start=max(ak[3],info[1]);end=min(bk[3],info[2]);window=dict(older_owner_end=ak[3],newer_owner_end=bk[3],older_sky_refresh=info[1],newer_sky_refresh=info[2],overlap_start=start,overlap_end=end);timing_windows.append(window)";assert text.count(marker)==1
text=text.replace(marker,"info=(Q*7)();assert sky_info(pair,info);ac=owner_times[ak][6];bc=owner_times[bk][6];assert ac<bc;start=max(ac,info[1]);end=min(bc,info[2]);window=dict(older_owner_end=ak[3],newer_owner_end=bk[3],older_camera_capture=ac,newer_camera_capture=bc,older_sky_refresh=info[1],newer_sky_refresh=info[2],overlap_start=start,overlap_end=end,end_convention_has_overlap=max(ak[3],info[1])<min(bk[3],info[2]));timing_windows.append(window)")
marker='target=(start+end)/2;alpha=(target-ak[3])/(bk[3]-ak[3]);';assert text.count(marker)==1;text=text.replace(marker,'target=(start+end)/2;alpha=(target-ac)/(bc-ac);')
marker="shared_time_error=abs((ak[3]+alpha*(bk[3]-ak[3]))-(info[1]+sky_alpha*(info[2]-info[1])))";assert text.count(marker)==1;text=text.replace(marker,'shared_time_error=abs((ac+alpha*(bc-ac))-(info[1]+sky_alpha*(info[2]-info[1])))')
text=text.replace("'owner-pose-report.json'","'capture-time-gpu-report.json'").replace('PASS_SHARED_OWNER_TIME_CAR_WORLD_SKY_DIAGNOSTIC','PASS_MEASURED_CAPTURE_TIME_CAR_WORLD_SKY_DIAGNOSTIC').replace('shared-owner-time-diagnostic.png','capture-time-diagnostic.png')
marker="assert pose_counts['coupled_4k_cases']>=1,(dict(pose_counts),timing_windows[:4])";assert text.count(marker)==1;text=text.replace(marker,marker+"\nassert pose_counts['no_positive_shared_time_window']==0 and len(timing_windows)==115\n")
p=out/('capture-time-real-'+hashlib.sha256(text.encode()).hexdigest()[:12]+'.py');p.write_text(text);r=subprocess.run([os.sys.executable,str(p)],capture_output=True,text=True,timeout=240);(out/'capture-time-gpu-test.log').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr,flush=True);r.check_returncode()
rows=json.loads((out/'diagnostic-route.json').read_text())['observations'];rows.sort(key=lambda r:(r['owner'][0],r['owner'][1]));pairs=[]
for a,b in zip(rows,rows[1:]):
 if a['owner'][0]!=b['owner'][0] or b['owner'][3]-a['owner'][3]>8:continue
 old=(max(a['owner'][3],a['sky_refresh']),min(b['owner'][3],b['sky_refresh']));actual=(max(a['timing'][6],a['sky_refresh']),min(b['timing'][6],b['sky_refresh']));assert actual[0]<actual[1]
 target=(actual[0]+actual[1])/2;ga=(target-a['timing'][6])/(b['timing'][6]-a['timing'][6]);sa=(target-a['sky_refresh'])/(b['sky_refresh']-a['sky_refresh']);assert 0<ga<1 and 0<sa<1
 pairs.append(dict(older_owner=a['owner'],newer_owner=b['owner'],completion_window=old,capture_window=actual,capture_target=target,geometry_alpha=ga,sky_alpha=sa,completion_window_has_overlap=old[0]<old[1]))
assert len(pairs)>100
report=dict(result='PASS_MEASURED_CAPTURE_TIME_BRACKETS',qualified_unique_source_owners=len(rows),adjacent_forward_pairs=len(pairs),capture_brackets_positive=len(pairs),completion_brackets_nonoverlap=sum(not r['completion_window_has_overlap'] for r in pairs),pairs=pairs,raw_input_sha256=sha(out/'diagnostic-route.json'),gpu_test_sha256=sha(Path(__file__)),source_camera_exactly_bound=True,object_rotation_capture_time_still_requires_per_model_policy=True,full_scene_60fps=False,live_enabled=False)
(out/'capture-time-bracket-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='pairs'},indent=2))
