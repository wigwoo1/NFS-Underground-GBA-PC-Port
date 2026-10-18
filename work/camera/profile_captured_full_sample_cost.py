import owned_endpoint_road_planner as planner
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
planner.endpoint_road_span_candidates=endpoint_road_span_candidates
import owned_road_planner_library_install_candidate,owned_road_material_decode_install_candidate,owned_preparation_fixed_types_install_candidate,owned_road_encode_flat_join_install_candidate,owned_road_record_worker_install_candidate
import cProfile,pstats,io,json
from pathlib import Path
setup=Path('work/camera/test_prepared_world_release_candidate.py').read_text().split('results=[]')[0];exec(compile(setup,'captured-profiler-setup','exec'))
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
prof=cProfile.Profile();outputs=[]
for i in range(12):
 local_history=EndpointRoadPlanner(rom,table);local_history.scratch=restore(local_history.d,h['scratch']);local_history.epoch=h['epoch'];local_history.refresh=h['refresh']
 local_prepared=PreparedWorldMotion(*frames,*scenes,local_history,roads,rom)
 prof.enable();cached=PrecomputedSourceWorldSamples(local_prepared,alphas);prof.disable()
 outputs.append([signature(cached.sample(a)) for a in alphas]);cached.close();local_prepared.close();local_history.close()
assert all(x==outputs[0] for x in outputs)
stream=io.StringIO();stats=pstats.Stats(prof,stream=stream).strip_dirs().sort_stats('tottime');stats.print_stats(35)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/vertex-conversion-profile-20261010');(cp/'captured-full-sample-cprofile.txt').write_text(stream.getvalue());prof.dump_stats(str(cp/'captured-full-sample.prof'));print(stream.getvalue())
