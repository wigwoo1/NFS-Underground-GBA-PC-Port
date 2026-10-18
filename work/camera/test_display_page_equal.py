import ctypes as C,json
from pathlib import Path
D=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));P=C.c_void_p
D.nf_layer_snapshot_create.restype=P
D.nf_layer_snapshot_add.argtypes=[P,P]
D.nf_layer_snapshot_destroy.argtypes=[P]
D.nf_layer_snapshot_display_page_equal.argtypes=[P,P]
def make(change=None,page=0):
 s=D.nf_layer_snapshot_create();r=C.create_string_buffer(100480)
 C.c_uint16.from_buffer(r,8).value=0x404|page
 for y in range(160):
  C.c_uint32.from_buffer(r,4).value=y
  if change:change(r,y)
  assert D.nf_layer_snapshot_add(s,r)
 return s
owners=[]
def case(name,change,expected,page=0):
 a=make(page=page);b=make(change,page);owners.extend([a,b]);assert D.nf_layer_snapshot_display_page_equal(a,b)==expected,name
case('equal',None,1)
case('hidden page writes',lambda r,y:C.c_uint8.from_buffer(r,128+0xa000).__setattr__('value',7),1)
case('OBJ and OAM updates',lambda r,y:(C.c_uint8.from_buffer(r,128+0x10000).__setattr__('value',7),C.c_uint8.from_buffer(r,128+0x18000+1024).__setattr__('value',3)),1)
case('visible page writes',lambda r,y:C.c_uint8.from_buffer(r,128+37).__setattr__('value',7),0)
case('last visible byte page1',lambda r,y:C.c_uint8.from_buffer(r,128+0xa000+38399).__setattr__('value',7),0,16)
case('BG palette',lambda r,y:C.c_uint8.from_buffer(r,128+0x18000+511).__setattr__('value',7),0)
case('one scanline BG transform',lambda r,y:C.c_uint8.from_buffer(r,8+0x28).__setattr__('value',1 if y==79 else 0),0)
assert not D.nf_layer_snapshot_display_page_equal(None,owners[0])
for s in owners:D.nf_layer_snapshot_destroy(s)
report={'status':'PASS','cases':8,'scope':'component displayed-page equality only; no live scene reuse or gameplay timing proof'}
Path('outputs/nfsug-native-renderer/camera-research/display-page-equality-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

