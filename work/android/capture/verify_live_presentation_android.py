from pathlib import Path
import hashlib,json,subprocess,zipfile
r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');b=Path(r'C:\NFSUG-Workspace');app=b/'NFSUG-android-local/app-live-runtime-tests';native=b/'NFSUG-android-background-jni-native-local';host=b/'NFSUG-live-presentation-host'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((app/'apk-build-report.json').read_text());v=json.loads((app/'live-presentation-android-report.json').read_text());n=json.loads((native/'capture-jni-build-report.json').read_text())
assert a['result']=='PASS_SIGNED_APK_BUILD' and a['runner']=='LivePresentationInstrumentation' and sha(Path(a['apk']))==a['sha256']==v['apk_sha256']
for name,digest in a['source_sha256'].items():assert sha(r/'work/android'/name)==digest,name
for name,digest in n['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/stage_capture.py','/build_capture.py')):assert sha(r/name)==digest,name
p=json.loads((native/'source-provenance.json').read_text())
for name,digest in p['unaltered_source_sha256'].items():assert sha(r/('outputs/nfsug-research' if name in ('native_span.c','native_span.h') else 'work')/name)==digest,name
with zipfile.ZipFile(a['apk']) as z:
 for target in n['targets']:assert hashlib.sha256(z.read('lib/'+target['abi']+'/libnfsug_android_core.so')).hexdigest()==target['sha256']
assert v['result']=='PASS_ANDROID_LIVE_PRESENTATION' and v['native_frames']>=9 and v['superseded_valid_frames']>0 and v['original_frames']>0 and v['screen_reference_pixels']==701784
for flag in ('moving_refreshes','pause_resume','mode_fallback_restart','context_recreated'):assert v[flag]
assert not v['real_time_pacing_verified'] and not v['full_scene_60fps'] and len(v['fixtures'])==2
for name,digest in v['fixtures'].items():assert sha(b/'NFSUG-complete-scene-gpu-fixtures'/name)==digest
log=(app/'live-presentation-logcat.txt').read_text(encoding='utf-8');assert 'CORE_OPEN frequency=16777216 cycles=280896' in log;assert v.get('profile_cpu_dispatch',{}).get('core_step',{}).get('calls',0)>0 # Shorter successful tests may finish before the 300-step periodic log.
assert 'PASS_ANDROID_LIVE_PRESENTATION' in (app/'live-presentation-instrumentation.log').read_text()
jdk=b/'android-tools/jdk-21.0.12.1+1/bin';tests=[]
for name,args in [('NativePresentationTest',[]),('NativePresentationSceneTest',[str(b/'NFSUG-background-owner-api-fixtures')]),('RoadBatchingTest',[str(b/'NFSUG-background-owner-api-fixtures')]),('PreparedSceneTest',[str(b/'NFSUG-background-owner-api-fixtures')]),('LitWallCacheTest',[str(b/'NFSUG-background-owner-api-fixtures')]),('CompactRoadHistoryTest',[str(next((b/'NFSUG-background-owner-api-fixtures').glob('owner-*.nrh')))])]:
 subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(r/'work/android/java'),'-d',str(host/'classes'),str(r/('work/android/tests/org/codex/nfsugpreview/'+name+'.java'))],check=True)
 text=subprocess.run([str(jdk/'java.exe'),'-Xmx192m','-cp',str(host/'classes'),'org.codex.nfsugpreview.'+name,*args],check=True,capture_output=True,text=True).stdout.strip();assert text.startswith('PASS_');tests.append(text)
old_build=json.loads((app/'pre-shared-apk-build-report.json').read_text())
for name,digest in a['source_sha256'].items():
 if name.startswith('java/') and (Path(name).name.startswith('Native') or Path(name).name in ('FrameView.java','PreviewAudio.java','TouchOverlay.java')):assert old_build['source_sha256'][name]==digest,name
baseline=json.loads((app/'pre-shared-live-presentation-android-report.json').read_text());assert v['unique_native_frames']>=3 and v['profile_cpu_dispatch']['road_dispatch']['calls']>0
assert v['legacy_scene_copies_avoided']>0 and v['complete_scene_aliases']>0
ui=json.loads((app/'preview-native-ui-android-report.json').read_text());assert ui['result']=='PASS_ANDROID_PREVIEW_NATIVE_UI' and ui['apk_sha256']==a['sha256'] and ui['event_assertions']==38 and ui['native_presentations']>=3 and ui['paused_activity_recreation'] and ui['normal_exit_releases_core']
for name,digest in ui['fixtures'].items():assert sha(b/'NFSUG-complete-scene-gpu-fixtures'/name)==digest
result=dict(result='PASS_LIVE_PRESENTATION_ANDROID_INTEGRATION',renderer_core_audio_touch_sources_unchanged=True,ordinary_ui_touch_event_assertions=38,ordinary_ui_recreation_preserves_shared_scene=True,legacy_scene_copies_avoided=v['legacy_scene_copies_avoided'],complete_scene_aliases=v['complete_scene_aliases'],legacy_mean_ms_before=baseline['profile_cpu_dispatch']['legacy_snapshot']['mean_ms'],legacy_mean_ms_after=v['profile_cpu_dispatch']['legacy_snapshot']['mean_ms'],tests=tests,unique_native_frames=v['unique_native_frames'],prepare_mean_ms_before=baseline['profile_cpu_dispatch']['draw_prepare']['mean_ms'],prepare_mean_ms_after=v['profile_cpu_dispatch']['draw_prepare']['mean_ms'],road_dispatch_mean_ms_before=baseline['profile_cpu_dispatch']['road_dispatch']['mean_ms'],road_dispatch_mean_ms_after=v['profile_cpu_dispatch']['road_dispatch']['mean_ms'],native_draw_mean_ms_before=baseline['profile_cpu_dispatch']['native_draw']['mean_ms'],native_draw_mean_ms_after=v['profile_cpu_dispatch']['native_draw']['mean_ms'],timing_scope='Sampled live CPU/driver timings on software emulator; scene scopes differ, not a matched performance benchmark or hardware FPS measurement',native_frames=v['native_frames'],original_frames=v['original_frames'],superseded_valid_frames=v['superseded_valid_frames'],screen_reference_pixels=v['screen_reference_pixels'],moving_refreshes=True,pause_resume=True,mode_fallback_restart=True,context_recreated=True,source_apk_native_fixture_hashes_verified=True,apk_sha256=a['sha256'],real_time_pacing_verified=False,full_scene_60fps=False,physical_arm64=False,published=False)
(app/'live-presentation-integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

