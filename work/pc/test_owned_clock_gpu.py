from pathlib import Path
import hashlib,json,subprocess,os
base=Path('C:/NFSUG-Workspace');old=base/'NFSUG-pc-pose-capture-timing-tests';out=base/'NFSUG-pc-owned-pose-timing-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
verified=json.loads((old/'identity-test-report.json').read_text())['test_sha256'];paths=[p for p in old.glob('capture-time-real-*.py') if sha(p)==verified];assert len(paths)==1
text=paths[0].read_text().replace('NFSUG-pc-pose-capture-timing-tests','NFSUG-pc-owned-pose-timing-tests').replace('owner-pose-draw.dll','timed-scenes.dll').replace("out/'capture-host.dll'","out/'timing-core.dll'").replace("b['core_sha256']","b['timing_core_sha256']")
marker="capture=fn(d,'nf_pc_source_frame_capture',[P,S],P)";assert text.count(marker)==1;text=text.replace(marker,"capture=fn(d,'nf_pc_source_frame_capture_timed',[P,S,P],P)")
marker='capture(C.byref(api),64*1024*1024)';assert text.count(marker)==1;text=text.replace(marker,'capture(C.byref(api),64*1024*1024,C.cast(timing_read,P))')
marker="owner_times={};pose_time_getter=fn(core,'nf_pc_source_pose_timing',[Q,U,U,U,P,S,P,S])";assert text.count(marker)==1
text=text.replace(marker,"timing_read=fn(core,'nfa_core_capture_pose_timing',[P,Q,U,U,U,P,S],S);frame_time=fn(d,'nf_pc_source_frame_pose_timing',[P,U,P,P]);scene_time=fn(d,'nf_pc_scene_motion_timing',[P,U,P,P]);pose_clock=fn(d,'nf_pc_scene_pose_alpha',[P,U,P,U,C.c_double,P]);owned_clock_checks=0")
marker='k=(Q*5)();w=(Q*16)();cam=C.create_string_buffer(56);assert owner(frame,role,k) and pose_time_getter(k[0],k[1],k[2],k[3],w,128,cam,56);owner_times[tuple(k)]=tuple(w)';assert text.count(marker)==1;text=text.replace(marker,'assert blob(frame_time,frame,role)==blob(scene_time,scene,role)')
marker='ac=owner_times[ak][6];bc=owner_times[bk][6];';assert text.count(marker)==1;text=text.replace(marker,"at=blob(scene_time,old,ar);bt=blob(scene_time,new,br);ac=struct.unpack_from('<Q',at,48)[0];bc=struct.unpack_from('<Q',bt,48)[0];")
marker="if pose_counts['coupled_4k_cases']>=2:return";assert text.count(marker)==1
text=text.replace(marker,"target=(start+end)/2;clock=C.c_double(-7);assert pose_clock(old,ar,new,br,target,C.byref(clock)) and abs(clock.value-(target-ac)/(bc-ac))<1e-12;pose_counts['owned_c_clock_checks']+=1\n  "+marker)
marker='target=(start+end)/2;alpha=(target-ac)/(bc-ac);sky_alpha=';assert text.count(marker)==1;text=text.replace(marker,'alpha=clock.value;sky_alpha=')
text=text.replace('capture-time-gpu-report.json','owned-clock-gpu-report.json').replace('capture-time-diagnostic.png','owned-clock-diagnostic.png').replace('PASS_MEASURED_CAPTURE_TIME_CAR_WORLD_SKY_DIAGNOSTIC','PASS_OWNED_C_CLOCK_CAR_WORLD_SKY_DIAGNOSTIC')
marker="assert pose_counts['no_positive_shared_time_window']==0 and len(timing_windows)==115";assert text.count(marker)==1;text=text.replace(marker,marker+" and pose_counts['owned_c_clock_checks']==115")
p=out/('owned-clock-real-'+hashlib.sha256(text.encode()).hexdigest()[:12]+'.py');p.write_text(text);r=subprocess.run([os.sys.executable,str(p)],capture_output=True,text=True,timeout=240);(out/'owned-clock-gpu-test.log').write_text(r.stdout+r.stderr);print(r.stdout+r.stderr,flush=True);r.check_returncode()
