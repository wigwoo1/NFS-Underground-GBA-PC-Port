from pathlib import Path
import sys,struct,json,ctypes as C
sys.path.insert(0,str(Path("work/pydeps").resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in ((0x02000000,0x40000),(0x03000000,0x10000),(0x04000000,0x10000)):u.mem_map(a,n)
u.mem_write(0x03000000,Path("work/camera/visibility-scene-0-iwram.bin").read_bytes())
rectaddr=0x02000000;faceaddr=rectaddr+64;ptsaddr=faceaddr+64;ixaddr=ptsaddr+64
points=struct.pack("<8h",-100,-100,0,0,100,100,300,200)
u.mem_write(ptsaddr,points);u.mem_write(ixaddr,struct.pack("<4H",0,1,2,3))
u.mem_write(faceaddr,struct.pack("<6I",ptsaddr,0,ixaddr,0,0,4))
results=[]
for bounds,expected in (((2,0,0,158),4),((0,0,0,158),4),((0,240,10,0),4),((0,240,0,0),4),((0,240,0,160),3)):
 left,right,top,bottom=bounds
 u.mem_write(rectaddr,struct.pack("<4i",left,top,right,bottom))
 u.reg_write(UC_ARM_REG_R0,rectaddr);u.reg_write(UC_ARM_REG_R1,faceaddr)
 u.reg_write(UC_ARM_REG_SP,0x0400ff00);u.reg_write(UC_ARM_REG_LR,0x03006000)
 u.emu_start(0x03005824,0x03006000,count=10000)
 actual=u.reg_read(UC_ARM_REG_R0);assert actual==expected,(bounds,actual)
 results.append(dict(bounds=bounds,original_classification=actual))
# Replay actual new failure through native source preparation.
sys.path.insert(0,str(Path("work/camera").resolve()))
setup=Path("work/camera/test_external_changed_parent_exit.py").read_text().split("gpu=C.CDLL")[0].replace("1791308040881565000","1791576203688794500").replace("from owned_prepared_world_motion import PreparedWorldMotion","from owned_prepared_world_segmented_candidate import PreparedWorldMotion")
env={};exec(setup,env)
try:
 from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
 samples=PrecomputedSourceWorldSamples(env["prepared"],(.2,.5,.8));samples.close()
 result=dict(result="PASS",original_arm_cases=results,actual_failure_pair_samples=3,scope="Original classifier rejects empty axes; complete saved source preparation. No live cadence or fullscene raster proof.")
 Path("outputs/nfsug-native-renderer/camera-research/original-empty-model-rectangle-20261009.json").write_text(json.dumps(result,indent=2));print(result)
finally:env["prepared"].close();env["history"].close()
