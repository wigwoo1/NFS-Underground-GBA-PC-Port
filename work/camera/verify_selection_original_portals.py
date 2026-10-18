"""Actual original draw rectangles joined to independently regenerated selection endpoints."""
import ctypes as C,csv,json,struct,hashlib,sys
from pathlib import Path
from scene_batches import batches
m=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'));prefix=m['prefix'];sources=json.loads(Path(prefix+'-dense-source-identity-verification.json').read_text());wanted={(r['identity'][2],r['identity'][3]):r for r in sources['original_endpoints']};first=min(k[0] for k in wanted);last=max(k[1] for k in wanted)
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p];assert crt._putenv_s(b'NF_TRACE_DRAW_FRAMEBUFFER',b'1')==0;assert crt._putenv_s(b'NF_CAPTURE_MODEL_VIEWS',b'1')==0
d=C.CDLL(str(Path(__file__).parent/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_world_trace.argtypes=[C.c_char_p];d.nf_native_scene_refresh.restype=C.c_uint
rom=Path(m['rom']);state=Path(m['state']);assert hashlib.sha256(rom.read_bytes()).hexdigest()==m['rom_sha256'].lower() and hashlib.sha256(state.read_bytes()).hexdigest()==m['state_sha256'].lower();trace=Path(prefix+'-selection-original-portals.bin');started=False
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
@Sink
def sink(ctx,e,data,n):return 1
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t];blob=C.create_string_buffer(rom.read_bytes());assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1) and d.nf_live_visibility_enable(blob,len(blob)-1,16*1024*1024);d.nf_live_surface_audit_enable(1)
exact={};d.nf_live_completed_draw_scene_packet.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];d.nf_scene_packet_free.argtypes=[C.c_void_p]
try:
 for row in csv.DictReader(Path(prefix+'-input.csv').open()):
  if d.nf_native_scene_refresh()>=first-1 and not started:assert d.nf_world_trace(str(trace).encode());started=True
  d.nf_frame(int(row['keys']))
  if d.nf_native_scene_refresh()>last:break
 d.nf_world_trace(None)
 for key,row in wanted.items():
  out=C.c_void_p();size=C.c_size_t();poses=C.create_string_buffer(144*56);count=C.c_uint();assert d.nf_live_completed_draw_scene_packet(row['identity'][0],row['identity'][1],C.byref(out),C.byref(size),poses,144,C.byref(count));raw=C.string_at(out,size.value);d.nf_scene_packet_free(out);path=Path(prefix+f"-exact-endpoint-{row['identity'][1]}.packet");path.write_bytes(raw);exact[key]=dict(data=raw,path=str(path),poses=poses.raw[:count.value*56])
finally:d.nf_close()
checks=[]
for batch in batches(trace):
 key=(batch['begin_refresh'],batch['end_refresh'])
 if key not in wanted:continue
 row=wanted[key];data=Path(row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'];s={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+j*12) for j in range(5))};world=struct.unpack_from('<I',s[2],4)[0];count=struct.unpack_from('<I',s[5],4)[0];ids=[struct.unpack_from('<5I',s[5],8+j*20) for j in range(count)];at=8+count*20;assert s[5][at:at+4]==b'NFB2';bounds=[struct.unpack_from('<4H',s[5],at+16+j*8) for j in range(count)];observed=[];obj=None
 for event in batch['events']:
  blocks=event['blocks'];pc=event['pc']
  if pc==0x03002628:obj=blocks[62][0]
  if pc==0x03000304:
   source=blocks[5][0];matches=[j for j in range(world) if ids[j][0]==2 and ids[j][2]==source];assert len(matches)==1
   rect=struct.unpack_from('<4H',blocks[1][1],226);ordinal=matches[0];observed.append(dict(kind='wall',ordinal=ordinal,original_bounds=rect,native_bounds=bounds[ordinal],exact=rect==bounds[ordinal],original_camera_matrix=list(struct.unpack('<12i',blocks[2][1]))))
  if pc==0x03003d4c:
   matches=[j for j in range(world,count) if ids[j][2]==obj];assert len(matches)==1
   left,top,right,bottom=struct.unpack('<4i',blocks[86][1]);rect=(left,right,top,bottom);ordinal=matches[0];observed.append(dict(kind='model',ordinal=ordinal,original_bounds=rect,native_bounds=bounds[ordinal],exact=rect==bounds[ordinal]))
 raw=exact[key]['data'];es={t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+j*12) for j in range(5))};ec=struct.unpack_from('<I',es[5],4)[0];ew=struct.unpack_from('<I',es[2],4)[0];eid=[struct.unpack_from('<5I',es[5],8+j*20) for j in range(ec)];ep=8+ec*20;assert es[5][ep:ep+4]==b'NFB2';eb=[struct.unpack_from('<4H',es[5],ep+16+j*8) for j in range(ec)]
 for item in observed:
  source=ids[item['ordinal']];matches=[j for j,x in enumerate(eid) if x[:3]==source[:3]];assert len(matches)==1;item['exact_draw_root_bounds']=eb[matches[0]];item['exact_draw_root_match']=tuple(item['original_bounds'])==eb[matches[0]]
  if item['kind']=='wall':
   order=list(struct.unpack_from('<'+str(struct.unpack_from('<I',es[3],4)[0])+'I',es[3],8));command=order.index(matches[0]);pose=struct.unpack_from('<7d',exact[key]['poses'],command*56);matrix=(C.c_int32*12)(*item['original_camera_matrix']);pos=(C.c_double*3)(*[-v for v in item['original_camera_matrix'][9:12]]);decoded=(C.c_double*7)();d.nf_pose_decode.argtypes=[C.c_void_p]*3;assert d.nf_pose_decode(matrix,pos,decoded);item['camera_position_error']=sum((pose[j]-decoded[j])**2 for j in range(3))**.5;item['camera_quaternion_error']=min(sum((pose[j]-decoded[j])**2 for j in range(3,7))**.5,sum((pose[j]+decoded[j])**2 for j in range(3,7))**.5);assert item['camera_position_error']<1e-12 and item['camera_quaternion_error']<1e-12
 checks.append(dict(interval=key,exact_endpoint_path=exact[key]['path'],rectangles=observed,distinct_wall_ordinals=len({r['ordinal'] for r in observed if r['kind']=='wall'}),model_polygon_rectangles=sum(r['kind']=='model' for r in observed)))
assert len(checks)==len(wanted) and all(c['distinct_wall_ordinals'] and c['model_polygon_rectangles'] for c in checks)
mismatches=sum(not r['exact'] for c in checks for r in c['rectangles']);r=dict(result='MISMATCH' if mismatches else 'PASS',mismatches=mismatches,exact_draw_root_mismatches=sum(not r['exact_draw_root_match'] for c in checks for r in c['rectangles']),trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),checks=checks,scope='Actual original wall dispatch state bounds and model polygon-classifier rectangles compared with original-pose native endpoint portals. Fractional recomputation, fullvisibility/occlusion and smooth60fps remain separate.');Path(prefix+'-selection-original-portals.json').write_text(json.dumps(r,indent=2));print(json.dumps(dict(result=r['result'],mismatches=mismatches,exact_draw_root_mismatches=r['exact_draw_root_mismatches'],scenes=len(checks),wall_ordinals=sum(c['distinct_wall_ordinals'] for c in checks),model_polygon_rectangles=sum(c['model_polygon_rectangles'] for c in checks))))
