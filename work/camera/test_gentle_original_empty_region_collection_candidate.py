from pathlib import Path
import sys,struct,json
sys.path.insert(0,str(Path("work/pydeps").resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0,str(Path("work/camera").resolve()))
setup=Path("work/camera/test_external_changed_parent_exit.py").read_text().split("gpu=C.CDLL")[0].replace("1791308040881565000","1791575541143887200").replace("from owned_prepared_world_motion import PreparedWorldMotion","from owned_prepared_world_segmented_candidate import PreparedWorldMotion")
env={};exec(setup,env)
try:
 queue=env["prepared"].pair.portal.sample(1)
 assert next(r for r in queue if r[0]==30)[1:3]==(2,0)
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
 for address,size in ((0x02000000,0x40000),(0x03000000,0x10000),(0x04000000,0x10000)):u.mem_map(address,size)
 u.mem_write(0x03000000,Path("work/camera/visibility-scene-0-iwram.bin").read_bytes())
 state=0x02000000;table=0x02001000
 u.mem_write(state+0x60,struct.pack("<I",table));u.mem_write(state+0xee,struct.pack("<H",len(queue)))
 u.mem_write(table,b"".join(struct.pack("<8H",*r,0) for r in queue))
 visits=[]
 def hook(cpu,address,size,ctx):
  if address==0x030027f0:
   visits.append((cpu.reg_read(UC_ARM_REG_R2),tuple(struct.unpack("<8H",cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),16)))[:7]))
   cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
  elif address==0x03005224:cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
 u.hook_add(UC_HOOK_CODE,hook)
 u.reg_write(UC_ARM_REG_R0,state);u.reg_write(UC_ARM_REG_SP,0x0400ff00);u.reg_write(UC_ARM_REG_LR,0x03006000)
 u.emu_start(0x03004d5c,0x03006000,count=10000)
 assert u.reg_read(UC_ARM_REG_PC)==0x03006000
 expected=[(mode,r) for mode in (0,1) for r in reversed(queue) if not r[5]&(8 if mode==0 else 0x88)]
 assert visits==expected,(visits,expected)
 assert (1,next(r for r in queue if r[0]==30)) in visits
 from owned_ordinary_model_visits import ordinary_model_visits
 from owned_model_record_owners import model_record_owners
 owners=model_record_owners(env["prepared"].pair,env["rom"])
 assert owners[0][18]==owners[1][18]==36
 assert next(v for v in ordinary_model_visits(env["scenes"][1].graph,queue) if v["object"]==36)["bounds"]==(2,0,0,158)
 from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
 samples=PrecomputedSourceWorldSamples(env["prepared"],(.2,.5,.8));samples.close()
 result=dict(result="PASS",original_arm_region_dispatches=len(visits),exact_original_dispatch_order=True,empty_bounds_preserved=True,owner36_record18_both_endpoints=True,precomputed_samples=3,scope="Original ARM collector with draw leaves bypassed; saved full-scene preparation and ownership. No live timing or pixel fidelity proof.")
 Path("outputs/nfsug-native-renderer/camera-research/gentle-empty-region-owner-repair-20261009.json").write_text(json.dumps(result,indent=2));print(result)
finally:
 env["prepared"].close();env["history"].close()
