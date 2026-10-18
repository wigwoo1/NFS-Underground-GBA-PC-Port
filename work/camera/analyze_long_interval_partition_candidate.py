"""Partition complete long API intervals without double-counting nested stages."""
import json,sys
from pathlib import Path

def union_ns(segments,begin,end):
    clipped=sorted((max(begin,a),min(end,b)) for a,b in segments if min(end,b)>max(begin,a))
    total=0;last=begin
    for a,b in clipped:
        total+=max(0,b-max(last,a));last=max(last,b)
    return total

def analyze(report):
    assert report['gc_trace_dropped']==0
    api=report['bounded_diagnostic_stats']['whole_run_api_intervals']
    ledger=api['long_intervals']
    assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])==api['over_33_333ms']
    gc=[(x['start_ns'],x['end_ns']) for x in report['gc_collection_samples']]
    rows=[]
    for e in ledger['records']:
        begin,end=e['begin_ns'],e['end_ns'];span=end-begin
        assert span==e['interval_ns'] and span>0
        stages=[(e['draw_begin_ns'],e['draw_end_ns']),(e['present_begin_ns'],e['present_end_ns'])]
        assert all(b>=a for a,b in stages)
        stage=union_ns(stages,begin,end);collection=union_ns(gc,begin,end)
        combined=union_ns(stages+gc,begin,end)
        outside_gc=combined-stage;inside_gc=collection-outside_gc;uncovered=span-combined
        assert stage>=inside_gc>=0 and outside_gc>=0 and uncovered>=0
        assert stage+outside_gc+uncovered==span
        rows.append(dict(index=e['display_index'],interval_ms=span/1e6,draw_present_union_ms=stage/1e6,gc_inside_draw_present_ms=inside_gc/1e6,gc_outside_draw_present_ms=outside_gc/1e6,outside_stages_and_gc_ms=uncovered/1e6))
    return dict(result='LONG_INTERVAL_DISJOINT_STAGE_ACCOUNTING',total=len(rows),rows=sorted(rows,key=lambda x:x['outside_stages_and_gc_ms'],reverse=True),scope='Clipped wall-clock union partition; overlapping GC is not added twice. Uncovered time includes intentional pacing, queue waits and uninstrumented work. No exclusive CPU causality or scanout proof.')

if __name__=='__main__':
    out=analyze(json.loads(Path(sys.argv[1]).read_text()))
    Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
    print(out['result'],out['total']);print(out['rows'][:5])
