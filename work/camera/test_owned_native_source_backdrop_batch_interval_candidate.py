import sys,json,time,threading
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
from owned_sample_signature import signature
report=json.loads(Path(sys.argv[1]).read_text());meta=report['live_preparation_profiles'][0];folder=Path(meta['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_scene_setup','exec'));prepared.close();history.close()
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()));expected=json.loads((folder/'prepared-signatures.json').read_text())

import ctypes as C,hashlib
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
from owned_source_draw_context_candidate import OwnedSourceDraw
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None;cached=None
from owned_native_source_backdrop_batch_worker_candidate import NativeSourceWorker
from owned_native_source_commit_adapter_candidate import NativeSourceCommitAdapter,P
from owned_native_source_interval_candidate import NativeSourceInterval
from owned_motion_clock import scene_samples
session=None;results=[]
try:
 prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);older,newer=[scene.graph.refresh for scene in scenes];slots=scene_samples(0,older,older,newer,12);cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in slots),trace=True)
 boundaries=[]
 for scene in scenes:
  record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
  origin=record['asset_origin'];offset=record['source']-0x08000000
  boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
 origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
 session=NativeSourceWorker();authority=C.CDLL(str(Path('work/camera/owned-draw-commit-candidate.dll').resolve()));authority.nf_owned_handoff_create.argtypes=[C.c_uint64];authority.nf_owned_handoff_create.restype=P;authority.nf_owned_handoff_destroy.argtypes=[P]
 epoch=scenes[0].graph.epoch;owner=authority.nf_owned_handoff_create(epoch);assert owner
 origin=time.perf_counter_ns()+30000000-slots[0]['deadline_ns'];adapter=NativeSourceCommitAdapter(session,owner)
 results=NativeSourceInterval(adapter).render(cached,asset,boundaries,origin,older,older,newer,12,epoch,1,diagnostic=False)
 assert len(results)==len(slots);assert [r['slot']['index'] for r in results]==[r['index'] for r in slots]
 assert all(r['native_result']==-1 and r['presentation']['status']==3 for r in results)
 assert all('native_rgb_sha256' not in r['prepared'] for r in results)

finally:
 if 'owner' in globals():authority.nf_owned_handoff_destroy(owner)
 if session is not None:session.close();assert not session.thread.is_alive()
 if cached is not None:cached.close()
 if prepared is not None:prepared.close()
 history.close()
r=dict(result='NATIVE_INTERVAL_NO_READBACK_CPU_PROFILE',older_refresh=older,newer_refresh=newer,base_refresh=older,delay_refreshes=12,clock_hz=16777216,cycles_per_refresh=280896,frames=results,scope='Captured real scene interval sampled using unchanged original cycle clock and60Hz grid, actual native wait/D3D callbacks. Every slot attempted, no source logic advancement. All native presents occluded; not successful scanout, live-game timing or60fps proof.')
Path(sys.argv[2]).write_text(json.dumps(r,indent=2));print(r['result'],older,newer,len(results))
