import os,sys
from pathlib import Path
if __name__=='__main__':
 for name,value in dict(NFSUG_HUD_CALLBACK_STAGE_BATCH='1',NFSUG_ROAD_FLAT_JOIN='1',NFSUG_ROAD_RECORD_CONSTRUCTION='1',NFSUG_FRAME_PREFIX_CACHE='1',NFSUG_STREAMING_OUTPUT='1',NFSUG_ROAD_MATERIAL_RESOLUTION='0',NFSUG_CHILD_STARTUP_GC='1').items():os.environ[name]=value
 import owned_hud_callback_stage_batch_candidate as batch
 batch.install()
 path=Path(__file__).with_name('run_native_long_sky_linear_candidate.py')
 text=path.read_text()
 needle=" try:exec(compile(source,'bounded-segmented-live-process'"
 assert text.count(needle)==1
 insertion=" source=source.replace(' import owned_hud_borrowed_rows_install_candidate\\n',' import owned_hud_borrowed_rows_install_candidate\\n import current_launcher_sky_pixels\\n')\n"
 text=text.replace(needle,insertion+needle)
 try:exec(compile(text,str(path),'exec'),dict(__name__='__main__',__file__=str(path)))
 finally:
  if 'current_launcher_sky_pixels' in sys.modules:sys.modules['current_launcher_sky_pixels'].save()
  batch.uninstall()
