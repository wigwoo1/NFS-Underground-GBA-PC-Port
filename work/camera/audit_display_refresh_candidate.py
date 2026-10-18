"""Audit observed flip-model display IDs; sampled statistics do not prove unseen frames dropped."""
import json,sys,collections,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());p=json.loads(Path(sys.argv[2]).read_text());a=[s for s in r['presentation_samples'] if s.get('presentation_backend')=='dxgi_flip_sequential'];assert len(a)==len(p['rows']) and not p['dropped']
sub={};observed={};repeats=0
for s,t in zip(a,p['rows']):
 assert t[0]==s['epoch'] and t[5]==0 and t[6]==t[4];sub[t[6]]=dict(epoch=s['epoch'],display_index=s['display_index'],refresh=s['refresh'],alpha=s['alpha'])
 if t[7]!=0 or not t[8] or not t[11]:continue
 assert t[8] in sub and t[8]<=t[6]
 if t[8] in observed:
  assert observed[t[8]]['present_refresh']==t[9];repeats+=1;continue
 observed[t[8]]=dict(present_id=t[8],present_refresh=t[9],sync_refresh=t[10],sync_qpc_ns=t[11]*1000000000//t[3],render=sub[t[8]])
rows=list(observed.values());gaps=[];increments=[]
for x,y in zip(rows,rows[1:]):
 assert y['present_id']>x['present_id'] and y['present_refresh']>x['present_refresh'];delta=y['present_refresh']-x['present_refresh'];increments.append(delta)
 if delta>1:
  exact=x['sync_refresh']==x['present_refresh'] and y['sync_refresh']==y['present_refresh']
  overlap=exact and any(x['sync_qpc_ns']<v['end_ns'] and y['sync_qpc_ns']>v['begin_ns'] for v in r['pause_events'])
  gaps.append(dict(before=x['present_id'],after=y['present_id'],refresh_delta=delta,present_id_delta=y['present_id']-x['present_id'],pause_overlap=overlap if exact else None,qpc_is_present_refresh=exact,render_before=x['render'],render_after=y['render']))
missing=sorted(set(sub)-set(observed));out=dict(result='DISPLAY_CADENCE_INCOMPLETE',submissions=len(sub),observed_ids=len(observed),repeated_stat_observations=repeats,unobserved_ids=missing,refresh_increment_counts=dict(collections.Counter(increments)),multi_refresh_gaps=gaps,scope='Flip-model PresentCount IDs joined to exact successful submissions. Unobserved IDs may reflect sampling or shutdown tail; not classified dropped. SyncQPC is scheduler sample, only pauseclassified when SyncRefresh equals PresentRefresh at both ends. Execution desktop only, no physical4K/fullgame proof.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['multi_refresh_gaps','unobserved_ids']});print('consecutive active display gaps',sum(x['pause_overlap'] is False and x['present_id_delta']==1 for x in gaps));print('unobserved',len(missing),'gaps',len(gaps),'active',sum(x['pause_overlap'] is False for x in gaps))

