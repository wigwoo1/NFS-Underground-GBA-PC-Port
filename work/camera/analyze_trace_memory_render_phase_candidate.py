import json,sys,statistics,copy
from pathlib import Path
from analyze_trace_memory_candidate import analyze as validate_memory
def analyze(memory,tail):
 validate_memory(memory)
 commits=[x['commit_ns'] for x in tail['rows'] if x['commit_ns']>0];assert commits
 begin=min(commits);end=max(commits);assert begin<end
 samples=[x for x in memory['samples'] if begin<=x['time_ns']<=end];assert len(samples)>=100
 assert memory['samples'][0]['time_ns']<begin and memory['samples'][-1]['time_ns']>end
 # time_ns is perf_counter_ns in the actual observer, matching native QPC-derived records.
 def stats(key):
  values=[x[key] for x in samples];return dict(minimum=min(values),peak=max(values),first_five_second_median=statistics.median(values[:10]),last_five_second_median=statistics.median(values[-10:]),median_window_change=statistics.median(values[-10:])-statistics.median(values[:10]))
 return dict(result='PASS_NATIVE_COMMIT_PHASE_PARENT_MEMORY',samples=len(samples),native_commit_span_seconds=(end-begin)/1e9,retained_sample_span_seconds=(samples[-1]['time_ns']-samples[0]['time_ns'])/1e9,private_bytes=stats('private_bytes'),working_set_bytes=stats('working_set_bytes'),scope='Independent parent memory samples inside first-to-last successful native commit interval using same perf_counter/QPC clock. Includes pauses and startup rendering; no root attribution, child/GPU accounting or leak/stable-memory claim.')
if __name__=='__main__':
 memory=json.loads(Path(sys.argv[1]).read_text());tail=json.loads(Path(sys.argv[2]).read_text());out=analyze(memory,tail)
 bad=copy.deepcopy(memory)
 for x in bad['samples']:x['time_ns']+=10**18
 try:analyze(bad,tail)
 except AssertionError:out['unrelated_clock_negative_control']='PASS'
 else:raise AssertionError('Unrelated clock accepted')
 Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
