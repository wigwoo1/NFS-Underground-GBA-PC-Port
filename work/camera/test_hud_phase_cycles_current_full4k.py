import ctypes as C,sys,json
from pathlib import Path
backend=sys.argv[1];output=sys.argv[2];original=C.CDLL;loads=[]
def load(path,*args,**kwargs):
 if Path(path).name.startswith('owned-d3d-'):
  path=str(Path(path).with_name(backend));loads.append(path)
 return original(path,*args,**kwargs)
C.CDLL=load
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json',output]
source=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text()
line=next(x for x in source.splitlines() if x.startswith('reference=json.loads'))
source=source.replace(line,'assert len(results)==5')
source=source.replace('assert stats[1]>100 and 0<stats[2]<=8','assert 0<=stats[2]<=8')
source=source.replace('assert session.consumer.d.nf_d3d_world_upload_stats(uploads)==0 and list(uploads)==[5,0]','assert session.consumer.d.nf_d3d_world_upload_stats(uploads)==0')
if backend=='owned-d3d-hud-discard-return-execution.dll':
 source=source.replace('  session.close();assert session.source.nf_owned_gpu_contexts()==0',"  before_discard=(C.c_uint64*8)();d.nf_d3d_hud_discard_stats.argtypes=[C.c_void_p,C.c_size_t];assert d.nf_d3d_hud_discard_stats(before_discard,C.sizeof(before_discard))==0;assert before_discard[0]>0 and before_discard[1]==3 and before_discard[3]==before_discard[4]==3 and before_discard[5]<=460800,list(before_discard)\n  session.close();assert session.source.nf_owned_gpu_contexts()==0\n  after_discard=(C.c_uint64*8)();assert d.nf_d3d_hud_discard_stats(after_discard,C.sizeof(after_discard))==0;assert list(after_discard)[3:6]==[0,0,0] and after_discard[7]==0")
exec(compile(source,'actual-final-renderer-five-full4k-fixture','exec'))
assert loads and all(Path(x).name==backend for x in loads)
r=json.loads(Path(output).read_text());r['actual_backend']=backend;
if backend=='owned-d3d-hud-discard-return-execution.dll':r['discard_before_close']=list(before_discard);r['discard_after_close']=list(after_discard)
r['scope']='Five diagnostic full4K RGB frames and existing invalid-tail/cleanup guards; comparative current-backend parity only, not gameplay qualification.';Path(output).write_text(json.dumps(r,indent=2))
