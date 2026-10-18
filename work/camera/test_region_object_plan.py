"""Atomic composed eligibility/source planning on original-tested gate fixture."""
import runpy
v=runpy.run_path('work/camera/test_region_object_gate.py')
C=v['C'];struct=v['struct'];u=v['u'];d=v['d'];reader=v['reader'];reciprocal=v['reciprocal'];p=v['p'];json=v['json']
fn=d.nfs_visibility_region_object_plan
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,v['Read'],C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
state=bytearray(v['state']);struct.pack_into('<I',state,12,0x0200e000);struct.pack_into('<I',state,120,0x0200d000)
desc=bytearray(48);struct.pack_into('<H',desc,10,65535);u.mem_write(0x02001000,bytes(desc));u.mem_write(0x0200e000,struct.pack('<H',7));record=struct.pack('<8H',0,0,240,0,158,0,0,65535)
checks=0
for mode in ('accept','capacity','invalid_head','read_failure','skip','invalid_pass'):
 out=C.create_string_buffer(b'X'*4096,4096);count=C.c_uint(123);eligible=C.c_uint(456);s=bytearray(state);capacity=512;pas=1
 u.mem_write(0x0200e000,struct.pack('<H',7))
 if mode=='capacity':capacity=0
 if mode=='invalid_head':u.mem_write(0x0200e000,struct.pack('<H',512))
 if mode=='read_failure':struct.pack_into('<I',s,12,0x01000000)
 if mode=='skip':struct.pack_into('<I',s,120,0)
 if mode=='invalid_pass':pas=2
 status=fn(bytes(s),record,pas,reader,None,reciprocal,out,capacity,C.byref(count),C.byref(eligible))
 if mode=='accept':assert status==1 and count.value==1 and eligible.value==1 and out.raw[:8]==struct.pack('<2I',0,7)
 elif mode=='skip':assert status==1 and count.value==0 and eligible.value==0 and out.raw==b'X'*4096
 else:assert status==-1 and count.value==123 and eligible.value==456 and out.raw==b'X'*4096
 checks+=1
report=dict(result='PASS',composed_cases=checks,atomic_rejections=4,scope='Composed gate/source success, skip, capacity, invalid head, failed read and invalid pass; underlying gate original ARM test also run.')
(p/'region-object-plan-tests.json').write_text(json.dumps(report,indent=2));print(report)
