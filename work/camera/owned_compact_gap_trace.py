"""Scalar-only largest-gap retention, independent of arrival lateness."""
import heapq
from owned_fine_deadline_trace import Base

class CompactGapTrace(Base):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.gap_segments=[]
        self.gap_segments_dropped=0
        self.gap_previous=None
        self.gap_sequence=0

    def __copy__(self):
        result=super().__copy__()
        result.gap_segments=[dict(s,heap=s['heap'].copy()) for s in self.gap_segments]
        return result

    def observe(self,row):
        super().observe(row)
        if row['native_result']!=1:return
        key=(row['epoch'],row['generation'],row['display_index'])
        stamp=row['commit'][6]
        if not self.gap_segments or self.gap_segments[-1]['key']!=key[:2]:
            self.gap_segments.append(dict(key=key[:2],heap=[],intervals=0))
            if len(self.gap_segments)>16:
                self.gap_segments.pop(0);self.gap_segments_dropped+=1
        previous=self.gap_previous
        self.gap_previous=(key,stamp)
        if previous is None or previous[0][:2]!=key[:2] or previous[0][2]+1!=key[2]:return
        gap=stamp-previous[1]
        segment=self.gap_segments[-1];segment['intervals']+=1
        self.gap_sequence+=1
        heap=segment['heap']
        if len(heap)==8 and gap<=heap[0][0]:return
        # Fixed scalar tuple; no nested payload serialization on the frame path.
        stages=row.get('caller_stages') or {};caller=row['callback_timing']
        prepared=row.get('prepared') or {};dispatch=prepared.get('renderer_dispatch') or {}
        def span(data,start,end):
            return data[end]-data[start] if start in data and end in data else None
        values=(key,previous[1],stamp,
                span(stages,'preparation_take_begin_ns','preparation_take_end_ns'),
                span(stages,'pair_begin_ns','pair_ready_ns'),
                span(caller,'draw_begin_ns','draw_end_ns'),
                span(dispatch,'started_ns','completed_ns'),
                span(caller,'present_begin_ns','present_end_ns'),
                tuple(row['commit'][2:4]),row.get('alpha'),
                stages.get('preparation_take_begin_ns'),stages.get('preparation_take_end_ns'))
        event=(gap,self.gap_sequence,values)
        if len(heap)<8:heapq.heappush(heap,event)
        else:heapq.heapreplace(heap,event)

    def stats(self):
        out=super().stats()
        out['compact_gap_diagnostic']=dict(segment_capacity=16,per_segment_capacity=8,
            segments_dropped=self.gap_segments_dropped,
            segments=[dict(key=s['key'],intervals=s['intervals'],records=[
                dict(gap_ns=e[0],identity=e[2][0],begin_ns=e[2][1],end_ns=e[2][2],
                     take_ns=e[2][3],pair_ns=e[2][4],draw_ns=e[2][5],job_ns=e[2][6],present_ns=e[2][7],
                     source_pair=e[2][8],alpha=e[2][9],take_begin_ns=e[2][10],take_end_ns=e[2][11])
                for e in sorted(s['heap'],reverse=True)] ) for s in self.gap_segments],
            scope='Largest eight adjacent successful commit gaps per retained generation; scalar snapshots only. Filter by authoritative live segment indices. Base aggregate diagnostics still active; no scanout qualification.')
        return out

def install():
    import owned_fine_deadline_trace as trace
    import owned_native_transaction_interval_totals_candidate as module
    if module.LongIntervalTotals is CompactGapTrace:return
    if module.LongIntervalTotals is not trace.DeadlineTrace:
        raise RuntimeError('Unexpected selected deadline observer')
    module.LongIntervalTotals=CompactGapTrace
