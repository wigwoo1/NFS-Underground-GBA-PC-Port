"""Check complete current native callback rows before diagnostic eviction."""
import struct

def validate(row):
 result=row['native_result']
 if result not in (-1,0,1):raise ValueError('Unknown native result')
 if row.get('prepared') and row['prepared']['publication'][:3]!=[row['epoch'],row['generation'],row['display_index']]:raise ValueError('Prepared identity mismatch')
 if result!=1:
  if row['native_committed_sample'] is not None:raise ValueError('Cancelled frame has commit')
  return
 commit=row['native_committed_sample'];expected=[row['epoch'],row['generation'],row['source_older'],row['refresh'],row['display_index']]
 if not commit or commit!=row['commit'] or commit[:5]!=expected:raise ValueError('Native commit identity mismatch')
 if commit[5]!=struct.unpack('<Q',struct.pack('<d',row['alpha']))[0]:raise ValueError('Native commit alpha mismatch')
 if row['presentation']['status']!=0:raise ValueError('Successful commit without S_OK')
 t=row['callback_timing']
 if not row['transaction_begin_ns']<=t['draw_begin_ns']<=t['draw_end_ns']<=t['present_begin_ns']<=t['present_end_ns']<=commit[6]<=row['transaction_end_ns']:raise ValueError('Native callback order mismatch')
 if commit[6]<row['presentation_deadline_ns']:raise ValueError('Commit before original display deadline')
