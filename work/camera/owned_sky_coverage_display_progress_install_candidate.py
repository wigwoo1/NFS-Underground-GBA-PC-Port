"""Observe actual validated native transactions, including batched present path."""
import sys
import owned_native_transaction_identity_candidate as identity
import owned_segmented_display_placement_install_candidate as display
original=identity.validate
seen=0;last=None

def validate(row):
 global seen,last
 original(row)
 if row['native_result']!=1:return
 key=(row['epoch'],row['generation'],row['display_index'])
 if key==last:raise ValueError('Duplicate display observation')
 p=row['presentation'];display.progress.observe(key[:2],p['dxgi_display_stats'],dict(epoch=key[0],generation=key[1],display_index=key[2]));seen+=1;last=key
 pixels=sys.modules.get('owned_deferred_sky_coverage_pixels_install_candidate')
 stats=p['dxgi_display_stats']
 if pixels is not None and stats[0]==0 and stats[1]==0 and stats[3]>0:
  owner=display.progress.submissions.get(stats[3])
  if owner is not None:
   reported=(owner['epoch'],owner['generation'],owner['display_index'])
   for captured in (r for r in pixels.rows if (r['epoch'],r['generation'],r['index'])==reported):
    if 'display_report' not in captured:captured['display_report']=dict(native_identity=list(reported),observed_at_native_identity=list(key),statistics=list(stats))
identity.validate=validate
