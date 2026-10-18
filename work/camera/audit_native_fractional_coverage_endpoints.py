from pathlib import Path
import ctypes as C,json,struct,math
p=Path('work/camera');dll=C.CDLL(str((p/'road-span-padding-segmented.dll').resolve()));span=dll.nf_road_span_transition_at;padfn=dll.nf_road_span_padding_segmented;span.argtypes=padfn.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p];uv=C.CDLL(str((p/'road-pair-uv-continuous.dll').resolve())).nf_road_pair_uv_continuous;uv.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p];query=C.CDLL(str((p/'road-pair-query-continuous.dll').resolve())).nf_road_pair_query_continuous;query.argtypes=[C.c_double,C.c_double,C.c_void_p];ledger=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 cmd=road['command'];ring=road['clipped_ring'];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));bounds=(C.c_uint16*4)(*road['bounds']);writes=(C.c_int16*(38400*2))();assert ledger(data,len(ring),bounds,table,writes);original=(p/f'stable-road-{cmd}-all-original-samples.bin').read_bytes();expected={struct.unpack_from('<IB',original,i)[0]:struct.unpack_from('<IB',original,i)[1] for i in range(0,len(original),5)};payload=(p/f'road-{cmd}-index-texture.bin').read_bytes();w,h=struct.unpack_from('<2I',payload);plane=payload[8:];nu,nv=road['normalization'];actual={};coordinates_changed=0;duplicates=spill=0;missing_examples=[]
 for destination in expected:
  row,x=divmod(destination,240);source_row,source_x=writes[destination*2:destination*2+2];coordinates_changed+=(source_row,source_x)!=(row,x);duplicates+=source_row!=row;spill+=source_x!=x
 for row in range(160):
  edges=(C.c_double*8)();pad=(C.c_double*2)()
  if not(span(data,len(ring),row,table,edges) and padfn(data,len(ring),row,table,pad)):continue
  for x in range(240):
   pair=C.c_double()
   if not query(pad[1],x-pad[0],C.byref(pair)):continue
   sample=(C.c_double*2)();assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),pad[1],pair.value,table,sample);tx=2*math.floor(sample[0]/(65536*nu)*(w/2))+(math.floor(x-pad[0])&1);ty=math.floor(sample[1]/(65536*nv)*h);actual[row*240+x]=plane[(ty%h)*w+tx%w]
 missing=sorted(set(expected)-set(actual));extra=sorted(set(actual)-set(expected));different=[i for i in set(actual)&set(expected) if actual[i]!=expected[i]]
 for dest in missing[:8]:missing_examples.append(dict(destination=dest,source_row=writes[dest*2],source_x=writes[dest*2+1]))
 scheduled={}
 for dest in range(38400):
  row,x=writes[dest*2:dest*2+2]
  if row<0:continue
  edges=(C.c_double*8)();pad=(C.c_double*2)();coordinate=C.c_double();assert span(data,len(ring),row,table,edges) and padfn(data,len(ring),row,table,pad) and query(pad[1],x-pad[0],C.byref(coordinate))
  sample=(C.c_double*2)();assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),pad[1],coordinate.value,table,sample);tx=2*math.floor(sample[0]/(65536*nu)*(w/2))+(math.floor(x-pad[0])&1);ty=math.floor(sample[1]/(65536*nv)*h);scheduled[dest]=plane[(ty%h)*w+tx%w]
 scheduled_missing=len(set(expected)-set(scheduled));scheduled_extra=len(set(scheduled)-set(expected));scheduled_differences=sum(scheduled[i]!=expected[i] for i in set(scheduled)&set(expected));assert scheduled_missing==scheduled_extra==scheduled_differences==0
 checks.append(dict(scheduled_missing=scheduled_missing,scheduled_extra=scheduled_extra,scheduled_index_differences=scheduled_differences,command=cmd,original_covered=len(expected),candidate_covered=len(actual),missing=len(missing),extra=len(extra),index_differences=len(different),original_coordinates_changed_by_writeorder=coordinates_changed,original_different_source_row=duplicates,original_spill_source_x=spill,missing_examples=missing_examples))
report=dict(result='MEASURED_CANDIDATE_NOT_ADOPTED',destinations=115200,checks=checks,scope='Candidate direct integer-row coverage vs immutable original index oracle and independent native write ledger. Quantifies endpoint violations; not GPU/nativefractional motion proof.');(p/'native-fractional-coverage-endpoint-audit.json').write_text(json.dumps(report,indent=2));print(report)
