"""Summarize sampled shortage context without claiming an audible gap duration."""
from pathlib import Path
import argparse,hashlib,json
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace')
p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,default=base/'NFSUG-pc-audio-context-live-tests');out=p.parse_args().output_dir
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((out/'live-build-report.json').read_text());t=json.loads((out/'live-test-report.json').read_text());r=json.loads((out/'traffic-live-route-test-report.json').read_text());a=r['session']
assert r['result']=='VERIFIED_TRAFFIC_LIVE_ROUTE_LIMITED_PREVIEW' and r['audio_pcm_exact']
c=json.loads((out/'audio-queue-component-test-report.json').read_text());assert c['result']=='PASS_REAL_HOST_AUDIO_QUEUE_COMPONENT' and c['source_sha256']==sha(source/'live_host.c') and c['script_sha256']==sha(source/'test_audio_queue_component.py')
assert b['exe_sha256']==t['exe_sha256']==r['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe')
assert r['build_receipt_sha256']==sha(out/'live-build-report.json') and r['regression_receipt_sha256']==sha(out/'live-test-report.json')
for n,h in b['source_sha256'].items():assert sha(source/n)==h,n
assert len(a['audio_queue_empty_context'])==len(a['audio_queue_empty_pcm_frames'])==min(32,a['audio_queue_empty_events'])
events=[]
for event,frame in zip(a['audio_queue_empty_context'],a['audio_queue_empty_pcm_frames']):
 assert event['pcm_frame']==frame and event['previous_pcm_frame']<=frame and event['poll_interval_ms']>=0
 assert 0<=event['previous_queued_buffers']<=8 and 0<=event['pending_frames']<=65536 and 0<=event['previous_pending_frames']<=65536
 if not event['previous_poll_valid']:assert event['poll_interval_ms']==0
 events.append(dict(**event,producer_frames_since_previous_poll=frame-event['previous_pcm_frame'] if event['previous_poll_valid'] else None,poll_interval_in_original_steps=event['poll_interval_ms']/(280896/16777216*1000) if event['previous_poll_valid'] else None,full_block_already_in_ring_before_current_core_pull=event['pending_frames']>=2048))
report=dict(result='VERIFIED_SAMPLED_AUDIO_EMPTY_CONTEXT',exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],events=events,observed_empty_events=a['audio_queue_empty_events'],driver_polls=a['audio_queue_observations'],audio_pcm_exact=True,audio_dropped_frames=a['audio_dropped_frames'],original_wall_clock_budget_met=r['original_wall_clock_budget_met'],prepare_failures=a['prepare_failures'],known_late_source_gaps=r['late_capture_misses'],rough_project_percent=70,full_scene_60fps=False,audio_stutter_fixed=False,scope='Queue sampled before pulling current core PCM. Ring values and producer frame indices are not hardware playback positions. Poll interval does not measure audible gap duration; local AMD test does not establish Intel behavior.',source_sha256=sha(source/'live_host.c'),script_sha256=sha(Path(__file__)),live_route_receipt_sha256=sha(out/'traffic-live-route-test-report.json'),component_receipt_sha256=sha(out/'audio-queue-component-test-report.json'))
(out/'audio-empty-context-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
