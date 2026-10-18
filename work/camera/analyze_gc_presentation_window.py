"""Partition collections by recorded presentation window, never imply scanout."""
def analyze(report):
 rows=[r for r in report['presentation_samples'] if r.get('native_committed_sample')]
 assert rows
 begin=min(r['native_committed_sample'][6] for r in rows)
 end=max(r['present_end_ns'] for r in rows)
 groups={'before':[],'overlapping':[],'after':[]}
 for c in report['gc_collection_samples']:
  a,b=c['start_ns'],c['end_ns'];assert b>=a
  key='before' if b<=begin else 'after' if a>=end else 'overlapping'
  groups[key].append(dict(c,gc_wall_ms=(b-a)/1e6,window_overlap_ms=max(0,min(b,end)-max(a,begin))/1e6))
 return dict(scope='Recorded first native commit through last presentation return; startup/shutdown collections separately classified, no physical scanout claim.',begin_ns=begin,end_ns=end,groups=groups,max_overlapping_gc_ms=max((c['gc_wall_ms'] for c in groups['overlapping']),default=0),max_after_gc_ms=max((c['gc_wall_ms'] for c in groups['after']),default=0))
