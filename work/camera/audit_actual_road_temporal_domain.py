from pathlib import Path
import ctypes as C,json,collections
p=Path('work/camera');intervals=json.loads((p/'road-source-between-tests.json').read_text())['checks'];bounds={r['command']:r['bounds'] for r in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']};table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());clip=C.CDLL(str((p/'road-clip-continuous.dll').resolve())).nf_road_clip_continuous;clip.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];d=C.CDLL(str((p/'road-temporal-writes.dll').resolve()));writes=d.nf_road_temporal_writes;writes.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_double,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p];reason=d.nf_road_temporal_writes_rejection;reason.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_double,C.c_void_p,C.c_uint];reason.restype=C.c_uint;ledger=C.CDLL(str((p/'road-write-ledger.dll').resolve())).nf_road_write_ledger;ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];checks=[];endpoint_checks=0
for interval in intervals:
 cmd=interval['command'];bd=bounds[cmd];rings=[]
 for sample in interval['samples']:
  ring=[[r[0],r[1],r[1],r[2],r[3],r[4]] for r in sample['ring']];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));out=(C.c_double*768)();count=C.c_uint();assert clip(data,len(ring),bd[0],bd[1],table,out,128,C.byref(count));rings.append([(C.c_double*(count.value*6))(*out[:count.value*6]),count.value])
 a,na=rings[0];b,nb=rings[-1];phases=[]
 for sample,(current,nc) in zip(interval['samples'],rings):
  phase=sample['phase'];code=reason(a,na,b,nb,current,nc,(C.c_uint16*4)(*bd),phase,table,0)
  phases.append(dict(phase=phase,rejection_code=code,count=nc,ring=[list(current[i*6:i*6+6]) for i in range(nc)]))
  if phase in (0.,1.):
   assert code==0,(cmd,interval['begin_a'],phase,code);original=(C.c_int16*(38400*2))();assert ledger(current,nc,(C.c_uint16*4)(*bd),table,original)
   covered=[i for i in range(38400) if original[i*2]>=0];destinations=sorted(set(covered[::max(1,len(covered)//32)]+[0,239,38399]))
   for destination in destinations:
    out=(C.c_double*966)();count=C.c_uint();assert writes(a,na,b,nb,current,nc,(C.c_uint16*4)(*bd),phase,table,destination,out,322,C.byref(count));row,x=original[destination*2:destination*2+2];expected=[] if row<0 else [[row,x,1.]];assert [list(out[i*3:i*3+3]) for i in range(count.value)]==expected;endpoint_checks+=1
 checks.append(dict(command=cmd,begin_a=interval['begin_a'],begin_b=interval['begin_b'],phases=phases))
counts=collections.Counter(v['rejection_code'] for c in checks for v in c['phases'] if v['phase'] not in (0.,1.));report=dict(result='EXACT_ENDPOINTS_INTERIOR_DOMAIN_AUDITED',endpoint_winner_checks=endpoint_checks,interior_reason_counts=dict(counts),checks=checks,scope='18actualgame sourcepose intervals horizontal-clipped using currentlyretained sourcebounds.36endpoint sourcewinner samples exact despite changingoppositepose topology.54interiorphase domain checks; originalper-scene boundparity and unsupportedvisibility/topology handling remain.')
(p/'road-actual-temporal-domain-tests.json').write_text(json.dumps(report,indent=2));print(report['result'],endpoint_checks,dict(counts))
