from pathlib import Path
import runpy,ctypes as C,struct,json
p=Path('work/camera');scope=runpy.run_path(str(p/'sample_stable_fixed_unproject.py'));fn=scope['unproject'];table=scope['table'];b=(p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812-complete-stable-bundle.bin').read_bytes();h=struct.unpack_from('<8I',b);native=C.CDLL(str((p/'road-polygon-clip.dll').resolve())).nf_road_perspective_plan;native.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p];checks=0
for i in range(h[3]):
 _,_,offset,size=struct.unpack_from('<4I',b,32+i*16);asset=b[offset:offset+size];head=struct.unpack_from('<10I',asset)
 for j in range(head[5]):
  span=struct.unpack_from('<20I',asset,40+j*80)
  if span[2]!=0x03003190:continue
  c=span[4:];out=C.create_string_buffer(2048);final=C.create_string_buffer(64);n=C.c_uint();assert native(struct.pack('<16I',*c),table,out,32,C.byref(n),final);first=struct.unpack_from('<16I',out)
  for coordinate in (0,1):
   expected=C.c_int32(first[8+coordinate]-c[14+coordinate]).value;assert fn(c[10],C.c_int32(c[8+coordinate]).value)==expected;checks+=1
report=dict(result='PASS',captured_integer_unprojection_checks=checks,scope='Integer first-block unprojection exactly matches recovered perspective component on all retained wide original spans, offset removed modulo32. Fractional extension and fullscene/GPU motion unproven.');(p/'stable-road-fixed-unproject-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
