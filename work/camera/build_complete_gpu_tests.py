from pathlib import Path
import subprocess
p=Path(__file__).resolve().parent;root=p.parent.parent
compiler=Path('C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin')
common=['obj_tile','road_polygon_clip','road_near_attributes','render_submission','render_handoff','hardware_submission','layer_snapshot','presentation_submission','scene_packet','snapshot_store','presentation_timeline','rigid_motion','indexed_copy']
for name in ['stable_page','road_split','road_motion','prepared_motion']:
 subprocess.run([str(compiler/'gcc.exe'),'-B'+str(compiler)+'/', '-O2','-DNF_ROAD_ATTRIBUTE_CORRECTION','-DNF_DIAGNOSTIC_DEPTH','-DNF_SOURCE_COMMAND_ORDER','-DNF_TEST_ENDPOINT_BOUNDS',str(p/(name+'_gpu_test.c'))]+[str(p/(x+'.c')) for x in common]+['-lopengl32','-lgdi32','-luser32','-lm','-o',str(p/(name.replace('_','-')+'-gpu-test.exe'))],cwd=root,check=True)
