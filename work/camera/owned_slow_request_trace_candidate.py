"""Diagnostic-only retention of already measured slow-request phases."""
def retain(prepared,samples,transfers,started_ns):
 if samples is None:return dict(measured_samples=0,retained=False,reasons=[])
 timings=samples.sample_timings
 reasons=[]
 first_ready=None if not transfers else transfers[0]['ready_ns']-started_ns
 if first_ready is not None and first_ready>=32_000_000:reasons.append('first_ready_32ms')
 work_ns=[sum(stage['wall_ns'] for stage in x['source_sample_stages'] if stage['name']!='sample_publication') for x in timings]
 if any(value>=8_000_000 for value in work_ns):reasons.append('sample_preparation_8ms')
 result=dict(measured_samples=len(timings),retained=bool(reasons),reasons=reasons,first_ready_ns=first_ready)
 if not reasons:
  samples.sample_timings=[];samples.source_setup_stages=[]
  if prepared is not None:prepared.construct_stages=[]
 return result
