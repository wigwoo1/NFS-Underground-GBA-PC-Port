"""Reconcile native presentation authority with delayed Python batch telemetry."""
import math,struct

def reconcile(sample,epoch,generation,batch_rows,published=None):
 sample=tuple(sample);rows=tuple(batch_rows)
 if len(sample)!=8 or not rows or len(rows)>8:raise ValueError('Invalid batch snapshot')
 e,g,older,newer,index,bits,finished,serial=sample
 alpha=struct.unpack('<d',struct.pack('<Q',bits))[0]
 if e!=epoch or g!=generation or not older<newer or not math.isfinite(alpha) or not 0<=alpha<=1 or not finished or not serial:raise ValueError('Invalid native committed authority')
 keys=('source_older','refresh','display_index','alpha','generation')
 committed=dict(source_older=older,refresh=newer,display_index=index,alpha=alpha,generation=g,present_end_ns=finished)
 matches=[i for i,row in enumerate(rows) if row['display_index']==index]
 if len(matches)!=1:raise ValueError('Native commit outside retained active batch')
 position=matches[0]
 for i,row in enumerate(rows):
  if row.get('epoch')!=epoch or row.get('generation')!=generation:raise ValueError('Batch ownership changed')
  if i and row['display_index']!=rows[i-1]['display_index']+1:raise ValueError('Batch grid gap')
 if any(rows[position][key]!=committed[key] for key in keys):raise ValueError('Native batch identity mismatch')
 if published is not None:
  if published['display_index']>index:raise ValueError('Python publication ahead of native authority')
  if published['display_index']==index and any(published[key]!=committed[key] for key in keys):raise ValueError('Conflicting Python committed publication')
 cutoff=published['display_index'] if published is not None else -1
 return dict(last_committed=committed,unpublished_committed_indices=[row['display_index'] for row in rows[:position+1] if row['display_index']>cutoff],pending_indices=[row['display_index'] for row in rows[position+1:]])


def resolve_pause_snapshot(sample,has_sample,epoch,generation,batch_rows=(),published=None):
 """Resolve active prefix, previous published commit, or startup before commit."""
 rows=tuple(batch_rows);sample=tuple(sample)
 if has_sample not in (0,1) or len(sample)!=8 or len(rows)>8:raise ValueError('Invalid pause snapshot')
 for i,row in enumerate(rows):
  if row.get('epoch')!=epoch or row.get('generation')!=generation:raise ValueError('Retired active batch')
  if i and row['display_index']!=rows[i-1]['display_index']+1:raise ValueError('Batch grid gap')
 if not has_sample:
  if any(sample) or published is not None:raise ValueError('Missing native commit contradicts published frame')
  return dict(last_committed=None,unpublished_committed_indices=[],pending_indices=[r['display_index'] for r in rows])
 if rows and rows[0]['display_index']<=sample[4]<=rows[-1]['display_index']:
  return reconcile(sample,epoch,generation,rows,published)
 alpha=struct.unpack('<d',struct.pack('<Q',sample[5]))[0]
 if sample[0]!=epoch or not sample[1] or not sample[2]<sample[3] or not math.isfinite(alpha) or not 0<=alpha<=1 or not sample[6] or not sample[7]:raise ValueError('Invalid previous native commit')
 previous=dict(source_older=sample[2],refresh=sample[3],display_index=sample[4],alpha=alpha,generation=sample[1],present_end_ns=sample[6])
 if published is None or any(published.get(k)!=v for k,v in previous.items() if k!='present_end_ns'):raise ValueError('Unreconciled previous native commit')
 if rows and rows[0]['display_index']!=sample[4]+1:raise ValueError('Previous commit does not precede active batch')
 return dict(last_committed=previous,unpublished_committed_indices=[],pending_indices=[r['display_index'] for r in rows])
