import json,copy
from pathlib import Path

def verify(m):
 rows=m['rows'];assert len(rows)==16
 seen=set()
 for r in rows:
  key=tuple(r['identity']);assert key not in seen;seen.add(key)
  t=r['native_transaction'];c=t['commit'];assert len(c)==8 and c[:2]+[c[4]]==r['identity']
  assert t['native_result']==1 and t['native_callback_count']==1 and t['native_batch_result']==0 and t['presentation']['status']==0
  assert r['begin_ns']<=r['end_ns']<=t['transaction_begin_ns']<=c[6]<=t['transaction_end_ns']
  assert c[6]>=t['wait'][1] and t['stages']==sorted(t['stages']) and len(t['stages'])==7
  assert t['stages'][4]<=c[6]
  ticks=r['native_tail_ticks'];assert len(ticks)==7 and ticks[0]>0 and ticks[1:]==sorted(ticks[1:])
 return dict(result='PASS_ALL_16_CAPTURE_NATIVE_PRESENT_BINDINGS',captures=len(rows),scope='Bounded GPU sky-stage/final pixels bound to successful native presents by exact owner identity and ordering. Not physical scanout or cadence certification.')
if __name__=='__main__':
 root=Path(r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port')
 p=max((root/'work/camera/prototype-runs').glob('live-sky-centers-*/manifest.json'),key=lambda p:p.stat().st_mtime);m=json.loads(p.read_text());out=verify(m);rejected=[]
 for kind in ('identity','missing','early','failed','duplicate'):
  b=copy.deepcopy(m);r=b['rows'][0]
  if kind=='identity':r['native_transaction']['commit'][4]+=1
  elif kind=='missing':r.pop('native_transaction')
  elif kind=='early':r['native_transaction']['commit'][6]=r['end_ns']-1
  elif kind=='failed':r['native_transaction']['presentation']['status']=1
  else:b['rows'][1]=copy.deepcopy(r)
  try:verify(b)
  except (AssertionError,KeyError):rejected.append(kind)
  else:raise AssertionError(kind+' accepted')
 out.update(manifest=str(p),rejected_mutations=rejected);Path('dedicated_sky_commit_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
