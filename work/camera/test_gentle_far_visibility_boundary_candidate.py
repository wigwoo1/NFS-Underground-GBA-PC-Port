from pathlib import Path
import sys,json,struct
sys.path.insert(0,str(Path("work/pydeps").resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x03000000,0x10000)
u.mem_write(0x03000000,Path("work/camera/visibility-scene-0-iwram.bin").read_bytes())
checks=[]
for depth in (0,8191,8192,8221,0xffffffff):
 u.reg_write(UC_ARM_REG_R12,depth)
 # Execute only cmp/bhs; stop before either branch's next instruction.
 u.emu_start(0x03002368,0x03002370,count=2)
 target=u.reg_read(UC_ARM_REG_PC)
 expected=0x0300262c if depth>=8192 else 0x03002370
 assert target==expected,(depth,hex(target))
 checks.append(dict(unsigned_depth=depth,branch_target=hex(target),culled=depth>=8192))
sys.path.insert(0,str(Path("work/camera").resolve()))
import owned_model_record_builder as module
import inspect
observed=[]
def capture(scene,visit,result,material):
 observed.append(dict(publication=scene.graph.refresh,source_refresh=scene.graph.graph.refresh,
  owner=visit["object"],depth=visit["depth"],bounds=visit["bounds"],allocated=visit["allocated"],
  flags=struct.unpack_from("<H",visit["source"],10)[0],material_result=result,material=list(material)))
source=inspect.getsource(module.ModelRecordBuilder._prepare)
needle="if self.lib.nfs_visibility_object_material_plan(owned_state,source,xyz,read,None,self.reciprocal,material)!=1 or material[3]!=0:raise ValueError('Unverified scenery material')"
assert source.count(needle)==1
source=source.replace(needle,"result=self.lib.nfs_visibility_object_material_plan(owned_state,source,xyz,read,None,self.reciprocal,material)\n   if result!=1 or material[3]!=0:capture(scene,visit,result,material);raise ValueError('Unverified scenery material')")
import textwrap
ns=dict(module.ModelRecordBuilder._prepare.__globals__,capture=capture)
exec(compile(textwrap.dedent(source),"far-material-diagnostic","exec"),ns)
module.ModelRecordBuilder._prepare=ns["_prepare"]
setup=Path("work/camera/test_external_changed_parent_exit.py").read_text().split("gpu=C.CDLL")[0].replace("1791308040881565000","1791576492416199100").replace("from owned_prepared_world_motion import PreparedWorldMotion","from owned_prepared_world_segmented_candidate import PreparedWorldMotion")
env={};error=None
try:
 exec(setup,env)
 from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
 samples=PrecomputedSourceWorldSamples(env["prepared"],(.2,.5,.8));samples.close()
except ValueError as e:error=str(e)
finally:
 for key in ("prepared","history"):
  if env.get(key) is not None:env[key].close()
assert error=="Unverified scenery material" and len(observed)==1
assert observed[0]["depth"]==8221 and observed[0]["material_result"]==0 and observed[0]["flags"]&2
out=dict(result="PASS",original_arm_boundary_cases=checks,captured_failure=observed,
 scope="Exact unsigned original depth boundary and native visibility0 on savedfar endpoint. No production transition fix, live timing, or raster proof.")
Path("outputs/nfsug-native-renderer/camera-research/gentle-far-visibility-boundary-20261009.json").write_text(json.dumps(out,indent=2));print(out)
