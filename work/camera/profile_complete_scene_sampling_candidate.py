import cProfile,pstats,io,json
from pathlib import Path
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0]
source=source.replace('from owned_prepared_world_motion import PreparedWorldMotion','from owned_prepared_world_segmented_candidate import PreparedWorldMotion')
exec(compile(source,'captured_scene_setup','exec'))
profiler=cProfile.Profile()
try:
 profiler.enable()
 for i in range(1,100):prepared.sample(i/100)
 profiler.disable()
 stream=io.StringIO();pstats.Stats(profiler,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(35)
 Path('work/camera/prototype-runs/complete-scene-sampling-profile.txt').write_text(stream.getvalue());print(stream.getvalue())
finally:prepared.close();history.close()
