"""Diagnostic-only direct entry point; does not clear requested child stage traces."""
import os,runpy
from pathlib import Path
if __name__=='__main__':
 for name,value in dict(NFSUG_HUD_CALLBACK_STAGE_BATCH='1',NFSUG_ROAD_FLAT_JOIN='1',NFSUG_ROAD_RECORD_CONSTRUCTION='1',NFSUG_FRAME_PREFIX_CACHE='1',NFSUG_STREAMING_OUTPUT='1',NFSUG_ROAD_MATERIAL_RESOLUTION='0',NFSUG_CHILD_STARTUP_GC='1').items():os.environ[name]=value
 print('DIRECT_ENDPOINT_PROFILE_ENTRY',dict((name,os.environ.get(name)) for name in ('NFSUG_ENDPOINT_VALIDATION_REUSE','NFSUG_PROGRESSIVE_CPU_TRACE','NFSUG_PROGRESSIVE_CYCLE_TRACE','NFSUG_PROGRESSIVE_FINE_TRACE','NFSUG_PROGRESSIVE_FINE_FIRST','NFSUG_PROGRESSIVE_FINE_LAST','NFSUG_CHILD_GC_TRACE')),flush=True)
 runpy.run_path(str(Path(__file__).with_name('run_native_hud_callback_batch_candidate.py')),run_name='__main__')
