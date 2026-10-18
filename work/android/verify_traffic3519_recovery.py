from pathlib import Path
import hashlib,json
source=Path(__file__).resolve().parent;root=source.parents[1];base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Traffic-20261017';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a_path=out/'gap3519-results/first-gap-report.json';assert a_path.exists(),'Wait for SAME session28602 terminal recovery report'
a=json.loads(a_path.read_text());h=json.loads((out/'host3519-results/host3519-report.json').read_text());assert a['paired_original_pixels_pcm_clocks_exact'] and h['original_pixels_pcm_clocks_exact'] and a['native']['missing_steps']==list(range(1,11))
w=a['step3519'];assert w['retained_retry_present'] and w['original_background']['present'] and w['source_background_retry']['present'] and w['refresh']==15360
assert a['original']['audio_frames']==a['native']['audio_frames']==h['runs'][0]['audio_frames']==h['runs'][1]['audio_frames']==2613770
assert a['original']['audio_sha256']==a['native']['audio_sha256']==h['runs'][0]['audio_sha256']==h['runs'][1]['audio_sha256']=='ad51c09d7bd60b7b7980903c340940a442853d55167c5c398dbf28fc1765f398'
assert w['timing']==h['step3519']['timing'] and w['capture_stats']==h['step3519']['capture_stats'] and len(w['owners'])==len(h['step3519']['owners'])
pairs={'background.bin':'background.bin','legacy-scene.bin':'bundle.bin'}
for i,(left,right) in enumerate(zip(w['owners'],h['step3519']['owners'])):
 assert [left[k] for k in ['serial','begin','end']]==[right[k] for k in ['serial','begin','end']]
 for kind in ['world','road','wall','proof']:
  assert left[kind]['present'] and right[kind]['present'];pairs['owner'+str(i)+'-'+kind+'.bin']='owner'+str(i)+'-'+kind+'.bin'
compared={};different=[]
for aname,hname in pairs.items():
 ap=out/'gap3519-results'/aname;hp=out/'host3519-results'/hname
 assert sha(ap)==a['frozen_component_sha256'][aname] and sha(hp)==h['frozen_component_sha256'][hname]
 equal=ap.read_bytes()==hp.read_bytes();compared[aname]=dict(android_sha256=sha(ap),host_sha256=sha(hp),byte_exact=equal)
 if not equal:different.append(aname)
report=dict(result='VERIFIED_ANDROID_WINDOWS_TRAFFIC3519_RECOVERY_BYTE_EXACT' if not different else 'RECOVERY_PASS_CROSS_PLATFORM_COMPONENT_BYTES_DIFFER',paired_steps=3540,initial_only_missing=list(range(1,11)),source_retained_recovered=True,host_android_audio_and_clock_exact=True,original_pixels_checked_within_platforms=True,cross_platform_component_bytes_exact=not different,different_components=different,components=compared,android_report_sha256=sha(a_path),host_report_sha256=sha(out/'host3519-results/host3519-report.json'),verifier_sha256=sha(Path(__file__)),full_scene_60fps=False,full_route_verified=False,release_allowed=False,scope='Bounded actual traffic endpoint and original-data/lifecycle tests. Full6000 source coverage, GPU/live motion, real-time timing and physical device remain separate.')
(out/'gap3519-results/traffic-recovery-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
