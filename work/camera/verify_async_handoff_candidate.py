"""Require background-copy shutdown evidence in addition to existing renderer checks."""
import json,sys
from pathlib import Path

def verify(r):
 assert r['result']=='SMOKE_COMPLETE' and r['error'] is None
 s=r['background_copy_shutdown'];assert s['thread_alive'] is False and s['pending']==0
 c=s['counts'];assert all(type(c[k]) is int and c[k]>=0 for k in ('admitted','published','retired','failed'))
 assert c['failed']==0 and c['admitted']==c['published']+c['retired']
 assert not r['shutdown_evidence']['gpu_thread_alive'] and r['shutdown_evidence']['native_owner_released']
 return dict(result='PASS_BACKGROUND_COPY_SETTLEMENT_AND_JOIN',counts=c,scope='Whole copy counts and joined shutdown; original-clock and image/cadence checks remain separate.')
if __name__=='__main__':
 out=verify(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
