"""Join authoritative native commit gaps with GC union intervals."""
from analyze_native_batch_gaps import analyze as gaps
from analyze_gc_stall_overlap import overlap

def analyze(report):
 result=gaps(report)
 rows={r['display_index']:r for r in report['presentation_samples'] if r.get('native_committed_sample')}
 for gap in result['largest']:
  index=gap['display_index'];begin=rows[index-1]['native_committed_sample'][6];end=rows[index]['native_committed_sample'][6]
  gap['gc_union_overlap_ms']=overlap(begin,end,report['gc_collection_samples'])
  assert 0<=gap['gc_union_overlap_ms']<=gap['gap_ms']+.0001
 result['scope']+=' GC union overlap is wall coincidence, not exclusive CPU or causal attribution.'
 return result
