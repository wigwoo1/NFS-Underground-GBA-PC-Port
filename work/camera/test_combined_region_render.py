from pathlib import Path
import ctypes as C,struct,json,os,subprocess
from PIL import Image,ImageChops
p=Path(__file__).resolve().parent
sct=lambda raw:{t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+i*12) for i in range(5))}
d=C.CDLL(str(p/'candidate-packet-test.dll'))
for name in ('wall','road'):getattr(d,'nf_scene_packet_insert_'+name).argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
d.nf_scene_packet_free.argtypes=[C.c_void_p]
old=(p/'object-replay-143-old.bin').read_bytes();new=(p/'object-replay-143-new.bin').read_bytes();meta=json.loads((p/'object-replay-143.json').read_text());q=json.loads((p/'object-replay-143-queue.json').read_text())
a=sct(old);ns=sct(new);n=struct.unpack_from('<I',a[2],4)[0]
roads={x['region']:x for x in json.loads((p/'object-replay-143-roads.json').read_text())}
baseclips=[[0]*4 for _ in range(n)];ordinal=0
for i in struct.unpack_from('<'+'I'*(n+1),a[3],8):
 if i!=0xffffffff:baseclips[i]=meta['bounds'][ordinal*4:ordinal*4+4];ordinal+=1
from region_anchors import root_anchors
from region_block import region_block
trace=json.loads((p/'texture-provenance-tests.json').read_text())
records=next(x['records'] for x in trace['region_invocation_samples'] if x['scene']==143)
batch=(p/'object-replay-143-sampled-queue.bin').read_bytes();regions=[]
for qi in reversed(range(struct.unpack_from('<I',batch)[0])):
 record=struct.unpack_from('<8H',batch,8+qi*2068)
 if not record[5]&8:regions.append(record[0])
reference=root_anchors(regions,records)
planner=C.CDLL(str(p/'visibility-probe.dll'))
planner.nf_root_region_anchors.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
roots=[r for r in records if r[4]==0x03004da4 and r[8]==0 and r[5]==0]
ids=(C.c_uint32*len(regions))(*regions);intervals=(C.c_uint32*(3*len(roots)))(*(v for r in roots for v in (r[0]&65535,r[6],r[7])))
slots=(C.c_uint32*21)()
assert planner.nf_root_region_anchors(ids,len(regions),intervals,len(roots),slots)
anchors=dict(zip(regions,list(slots)[1:1+slots[0]]));assert anchors==reference
entries=[]
for x in q:
 src=x['draw'][0];anchor=anchors[x['record'][0]]
 entries.append((anchor,src,'wall',p/f'queue-candidate-143-{src}.bin',x['identity'],x['record'][1:5]))
existing_sources={struct.unpack_from('<I',a[5],16+i*20)[0] for i in range(n)}
# Region order comes from the sampled root schedule; wall order from its plan.
rank={};next_rank=0;wall_slots={}
planner.nf_wall_insertions.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
captured=next(x for x in trace['dispatch_samples'] if x['serial']==143)
segplanner=C.CDLL(str(p/'scene-segments-test.dll'))
segplanner.nf_scene_segments.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
segplanner.nf_segment_wall_insertions.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
def packed_array(rows,width):return (C.c_uint32*(len(rows)*width))(*(v for row in rows for v in (row if row is not None else [0]*width)))
segment_rows=packed_array(records,9);segment_commands=packed_array(captured['commands'],6);segment_origins=packed_array(captured['origins'],12);segment_passes=packed_array(captured['wall_passes'],3)
segment_output=(C.c_uint32*4611)()
assert segplanner.nf_scene_segments(segment_rows,len(records),segment_commands,len(captured['commands']),segment_origins,segment_passes,segment_output)
for qi in reversed(range(struct.unpack_from('<I',batch)[0])):
 offset=4+qi*2068;record=struct.unpack_from('<8H',batch,offset+4)
 if record[5]&8:continue
 for di in range(struct.unpack_from('<I',batch,offset)[0]):
  source,wall_pass=struct.unpack_from('<2I',batch,offset+20+di*32)
  if wall_pass:continue
  if source in rank:raise ValueError('ambiguous source occurrence')
  rank[source]=next_rank;next_rank+=1
 region=record[0]
 block_sources=[struct.unpack_from('<I',batch,offset+20+di*32)[0] for di in range(struct.unpack_from('<I',batch,offset)[0]) if struct.unpack_from('<I',batch,offset+24+di*32)[0]==0]
 if any(x['record'][0]==region for x in q):
  matching=[r for r in roots if r[0]&65535==region]
  assert len(matching)<=1
  positions=[]
  if matching:
   root=matching[0]
   block=region_block(root,captured['commands'],captured['origins'],captured['wall_passes'])
   positions=block['prefix'];tail=block['prefix_tail']
  else:tail=anchors[region]
  retained=[(captured['commands'][j][2],j) for j in positions]
  sampled_array=(C.c_uint32*len(block_sources))(*block_sources)
  retained_array=(C.c_uint32*(len(retained)*2))(*(v for pair in retained for v in pair));insertions=(C.c_uint32*129)()
  if positions:
   matches=[i for i in range(segment_output[1]) if list(segment_output[515+i*4:518+i*4])==[1,positions[0],tail]]
   assert len(matches)==1
   assert segplanner.nf_segment_wall_insertions(segment_rows,len(records),segment_commands,len(captured['commands']),segment_origins,segment_passes,matches[0],sampled_array,len(block_sources),insertions)
  else:
   assert planner.nf_wall_insertions(sampled_array,len(block_sources),retained_array,len(retained),tail,insertions)
  for j in range(insertions[0]):
   source=insertions[1+j];assert source not in wall_slots
   wall_slots[source]=insertions[65+j]
 if region in roads:
  road=roads[region];src=road['descriptor']
  if src not in existing_sources:
   assert road['extracted'] and not road['alternate_material']
   entries.append((anchors[region],src,'road',p/f'road-candidate-143-{region}.bin',road['identity'],[0,240,0,160]))
  rank[src]=next_rank;next_rank+=1
assert set(wall_slots)=={x['draw'][0] for x in q}
entries=[(wall_slots[e[1]],*e[1:]) if e[2]=='wall' else e for e in entries]
assert all(x['draw'][1]==0 for x in q),'deferred wall insertion unsupported'
object_source=meta['identity'][2];rank[object_source]=next_rank
entries.append((meta['slot'],object_source,'wall',p/'object-candidate-143.bin',meta['identity'],meta['candidate_bounds']))
entries.sort(key=lambda e:(e[0],rank[e[1]]))
# Fixed independent regression expectation from the previously verified fixture.
assert [e[1] for e in entries]==[139910724,139890192,139911132,139911200,139890288,139910928,139938876]
images={};orders={}
for mode in ('baseline','object','combined'):
 raw=old;clips=list(baseclips);selected=[] if mode=='baseline' else entries[-1:] if mode=='object' else entries
 for offset,(anchor,src,kind,path,ident,bounds) in enumerate(selected):
  surface=path.read_bytes();out=C.c_void_p();size=C.c_size_t();identity=(C.c_uint32*5)(*ident)
  assert getattr(d,'nf_scene_packet_insert_'+kind)(raw,len(raw),surface,len(surface),identity,anchor+offset,C.byref(out),C.byref(size))
  raw=C.string_at(out,size.value);d.nf_scene_packet_free(out);clips.append(bounds)
 sections=sct(raw);count=len(clips);h=struct.unpack_from('<8I',raw)
 order=struct.unpack_from('<'+'I'*(count+1),sections[3],8)
 sources=[None if i==0xffffffff else struct.unpack_from('<I',sections[5],16+i*20)[0] for i in order];orders[mode]=sources
 expected=[]
 for j,i in enumerate(struct.unpack_from('<'+'I'*(n+1),a[3],8)):
  expected.extend(e[1] for e in selected if e[0]==j);expected.append(None if i==0xffffffff else struct.unpack_from('<I',a[5],16+i*20)[0])
 assert sources==expected
 stem=p/f'combined-143-{mode}';stem.with_suffix('.bin').write_bytes(raw)
 clip=struct.pack('<5Id',0x3150434e,h[4],h[5],h[6],count,.5)
 for i,b in enumerate(clips):clip+=sections[5][8+i*20:28+i*20]+struct.pack('<4H',*b)
 stem.with_suffix('.clips').write_bytes(clip)
 env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(stem.with_suffix('.clips')),NF_PREVIEW_PHASE='2',NF_PREVIEW_FRACTION='.5')
 subprocess.run([str(p/'sampled-clip-preview.exe'),str(stem.with_suffix('.bin')),str(p/'object-replay-143-new.bin'),str(stem)],env=env,check=True,capture_output=True)
 with Image.open(str(stem)+'-2.ppm') as im:images[mode]=im.convert('RGB')
 images[mode].save(str(stem)+'.png')
results=[]
for left,right in (('combined','baseline'),('combined','object'),('object','baseline')):
 diff=ImageChops.difference(images[left],images[right]);results.append(dict(pair=[left,right],pixels=sum(v!=(0,0,0) for v in diff.get_flattened_data()),bbox=diff.getbbox()))
report=dict(result='PASS',insertions=len(entries),orders=orders,comparisons=results,scope='Diagnostic composition with derived root anchors and sampled wall-plan sequence. All candidate identities and assets from older owned scene. Road eligibility and complete nested traversal remain unverified; not live gameplay.')
(p/'combined-region-render-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
# Isolate each appended surface against an empty command-filter control.
isolated=[];env['NF_CAPTURE_CLIPS']=str(p/'combined-143-combined.clips')
for index in [999]+list(range(n,n+len(entries))):
 env['NF_ONLY_SURFACE']=str(index);prefix=p/f'combined-143-isolated-{index}'
 subprocess.run([str(p/'isolated-clip-preview.exe'),str(p/'combined-143-combined.bin'),str(p/'object-replay-143-new.bin'),str(prefix)],env=env,check=True,capture_output=True)
 with Image.open(str(prefix)+'-2.ppm') as im:current=im.convert('RGB')
 if index==999:empty=current;continue
 diff=ImageChops.difference(current,empty)
 isolated.append(dict(source=entries[index-n][1],kind=entries[index-n][2],pixels=sum(v!=(0,0,0) for v in diff.get_flattened_data()),bbox=diff.getbbox()))
report['isolated']=isolated
(p/'combined-region-render-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(isolated))








