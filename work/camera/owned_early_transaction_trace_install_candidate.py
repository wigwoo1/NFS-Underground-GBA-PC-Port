"""Bounded complete early transaction timing; no render-loop file writes."""
import json
from pathlib import Path
import owned_transaction_display_progress_install_candidate
import owned_native_transaction_identity_candidate as identity
original=identity.validate;rows=[];keys=set()
def validate(row):
 original(row)
 if row['native_result']!=1 or row['display_index']>180:return
 key=(row['epoch'],row['generation'],row['display_index'])
 assert key not in keys and len(rows)<180;keys.add(key)
 tx=row['native_transaction'];p=row['presentation'];c=row['commit'];t=row['callback_timing']
 rows.append(dict(identity=list(key),source_older=row['source_older'],source_newer=row['refresh'],alpha=row['alpha'],deadline_ns=row['presentation_deadline_ns'],commit_ns=c[6],caller_timing=dict(t),present_stages=dict(tx['presentation']['present_stage_ns']),wait=list(tx['wait']),dispatch=dict(tx['renderer_dispatch']),statistics=list(p['dxgi_display_stats'])))
identity.validate=validate
def save():
 assert rows
 p=Path('work/camera/prototype-runs')/('early-transaction-trace-'+str(rows[0]['commit_ns'])+'.json')
 p.write_text(json.dumps(dict(rows=rows,capacity=180,scope='All successful first180 native display indices; complete scalar timing and authoritative DXGI stats. No mask backend, no render-loop hashing/files; trace overhead remains.'),indent=2));print('EARLY_TRANSACTION_TRACE',p,flush=True)
