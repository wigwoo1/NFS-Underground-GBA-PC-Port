from pathlib import Path
import ctypes as C,random,struct,json
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nfs_visibility_object_sorted_plan;fn.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
r=random.Random(2204);emitted=0;rejections=0
for trial in range(500):
 count=r.randrange(1,513);order=r.sample(range(count),r.randrange(count+1));pool=bytearray(count*164)
 for i in range(count):struct.pack_into('<H',pool,i*164+4,65535)
 for i,node in enumerate(order):struct.pack_into('<H',pool,node*164+4,order[i+1] if i+1<len(order) else 65535)
 head=order[0] if order else 65535;out=(C.c_uint32*512)();amount=C.c_uint();assert fn(bytes(pool),count,head,out,512,C.byref(amount)) and list(out[:amount.value])==order;emitted+=len(order)
 if order:
  sentinel=C.create_string_buffer(b'X'*2048,2048);n=C.c_uint(777);assert not fn(bytes(pool),count,head,sentinel,len(order)-1,C.byref(n)) and sentinel.raw==b'X'*2048 and n.value==777;rejections+=1
  struct.pack_into('<H',pool,order[-1]*164+4,head);assert not fn(bytes(pool),count,head,sentinel,512,C.byref(n)) and sentinel.raw==b'X'*2048 and n.value==777;rejections+=1
  struct.pack_into('<H',pool,order[-1]*164+4,count);assert not fn(bytes(pool),count,head,sentinel,512,C.byref(n)) and sentinel.raw==b'X'*2048 and n.value==777;rejections+=1
report=dict(result='PASS',random_plans=500,planned_objects=emitted,atomic_rejections=rejections,scope='Ordered linked-list plan, empty lists, capacity failure, cycles and out-of-range links. Original dispatch comparison supplied by three sampled scene oracle runs.')
(p/'object-sorted-plan-tests.json').write_text(json.dumps(report,indent=2));print(report)
