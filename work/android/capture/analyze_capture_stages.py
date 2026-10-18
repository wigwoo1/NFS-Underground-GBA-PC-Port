from pathlib import Path
import hashlib,json,shutil,zipfile
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port')
base=Path(r'C:\NFSUG-Workspace')
out=base/'NFSUG-Android-Capture-Stage-Final-20261017';folder=out/'runtime-results'
summary=json.loads((folder/'reuse-runtime-summary.json').read_text())
assert summary['result']=='PASS_REUSE_GPU_LIVE_UI_REGRESSIONS'
profile=summary['live']['profile_cpu_dispatch']
names=['capture_background_copy','capture_background_bind_inclusive','capture_background_parse','capture_history_copy','capture_history_parse','capture_road_retention','capture_wall_retention','capture_prepared_constructor']
assert all(profile[n]['calls']>0 for n in names)
outer=profile['complete_capture']['total_ms'];accounted=sum(profile[n]['total_ms'] for n in names)
assert profile['capture_background_copy']['calls']<=profile['complete_capture']['calls']
assert 0<accounted<=outer
nested=profile['capture_world_copy_nested_in_bind']
assert nested['total_ms']<=profile['capture_background_bind_inclusive']['total_ms']
stages=sorted([dict(name=n,**profile[n],fraction_of_measured_capture=profile[n]['total_ms']/outer) for n in names],key=lambda row:row['total_ms'],reverse=True)
report=dict(result='VERIFIED_CAPTURE_STAGE_PROFILE_LIMITED_SCOPE',complete_capture=profile['complete_capture'],ranked_nonoverlapping_capture_stages=stages,nested_world_copy=nested,accounted_ms=accounted,unattributed_ms=outer-accounted,
            nested_world_copy_not_added_twice=True,isolated_fixture_root=summary['live']['isolated_fixture_root'],steady_state=False,physical_device=False,full_scene_60fps=False,
            limits='Short emulator lifecycle sample with startup, mode switches and GPU reference/readback. Means have different call counts; rank total time within this one sample. Binding includes world-copy time; do not add nested time again. This profiles existing work, not a sustained FPS/audio or cross-device benchmark.')
(folder/'capture-stage-analysis.json').write_text(json.dumps(report,indent=2),encoding='utf8')
dest=root/'outputs/nfsug-native-renderer/camera-research/android-capture-stage-profile-20261017';files={};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def copy(source,target):
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);assert sha(source)==sha(target);files[str(target.relative_to(dest))]=sha(target)
restore=json.loads((folder/'restoration-receipt.json').read_text());assert restore['owned_emulator_stopped'] and restore['installed_apk_sha256']=='4349f1a440e37e9b359aa25d34d98088ae202b198d7b15ce487cb6436d66256c'
for path in folder.iterdir():
 if path.is_file():copy(path,dest/'runtime-results'/path.name)
for variant in ['production','reuse-test']:
 receipt=json.loads((out/variant/'apk-build-report.json').read_text());assert sha(out/variant/'NFSUG-Android-Core-Preview.apk')==receipt['sha256']
 for name,h in receipt['source_sha256'].items():assert sha(root/'work/android'/name)==h,name
 for name in ['apk-build-report.json','NFSUG-Android-Core-Preview.apk']:copy(out/variant/name,dest/variant/name)
for name in ['java/org/codex/nfsugpreview/NativeCore.java','java/org/codex/nfsugpreview/NativeRetainedScene.java','java/org/codex/nfsugpreview/NativeWorkProfile.java','java/org/codex/nfsugpreview/GameSession.java','instrumentation/org/codex/nfsugpreview/LiveTestActivity.java','instrumentation/org/codex/nfsugpreview/LivePresentationInstrumentation.java','capture/run_capture_stage_final_android.py']:
 copy(root/'work/android'/name,dest/'source'/name)
protected={root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba':'53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593',root/'work/integration-0.state':'49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104'}
for p,h in protected.items():assert sha(p)==h
with zipfile.ZipFile(out/'production/NFSUG-Android-Core-Preview.apk') as a,zipfile.ZipFile(base/'NFSUG-Android-Image-Reuse-20261017/production/NFSUG-Android-Core-Preview.apk') as b:
 for abi in ['x86_64','arm64-v8a']:
  key='lib/'+abi+'/libnfsug_android_core.so';assert a.read(key)==b.read(key)
(dest/'checkpoint-receipt.json').write_text(json.dumps(dict(result='PASS_CAPTURE_STAGE_INSTRUMENTATION_AND_REGRESSIONS',files=files,protected_rom_state={str(p):h for p,h in protected.items()},native_libraries_unchanged=True,restoration=restore,terminal=True),indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
