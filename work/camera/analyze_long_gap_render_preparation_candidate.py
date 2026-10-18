"""Account retained long native gaps without claiming exclusive CPU attribution."""
import json,sys
from pathlib import Path
from analyze_native_transaction_long_intervals_candidate import analyze
p=Path(sys.argv[1]);raw=json.loads(p.read_text());audit=analyze(raw);rows=[]
for e in raw['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals']['records']:
 t=e['caller_timing'];prepared=e['prepared'];dispatch=prepared['renderer_dispatch']
 assert dispatch['kind']=='prepare'
 assert t['draw_begin_ns']<=dispatch['submitted_ns']<=dispatch['started_ns']<=dispatch['completed_ns']<=t['draw_end_ns']
 source=prepared['source_prepare_ns'];stages=prepared['consumer_stages'];consumer=sum(x['elapsed_ns'] for x in stages)
 execution=dispatch['completed_ns']-dispatch['started_ns'];residual=execution-source-consumer
 assert source>=0 and all(x['elapsed_ns']>=0 for x in stages) and residual>=0
 spans=[dispatch['submitted_ns']-t['draw_begin_ns'],dispatch['started_ns']-dispatch['submitted_ns'],execution,t['draw_end_ns']-dispatch['completed_ns']]
 assert sum(spans)==t['draw_end_ns']-t['draw_begin_ns']
 rows.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],gap_ms=e['interval_ns']/1e6,draw_ms=sum(spans)/1e6,dispatch_wait_ms=spans[1]/1e6,source_prepare_ms=source/1e6,consumer_ms={x['stage']:x['elapsed_ns']/1e6 for x in stages},execution_residual_ms=residual/1e6,outer_ms=(spans[0]+spans[3])/1e6))
out=dict(result='PASS_LONG_GAP_RENDER_PREPARATION_ACCOUNTING',count=len(rows),rows=sorted(rows,key=lambda x:x['gap_ms'],reverse=True),scope='Complete zero-drop >25ms commit ledger; elapsed renderer execution decomposed into reported source/consumer spans and residual. Scheduling can affect every span; residual is not exclusive CPU, and no scanout proof.')
p.with_name(p.stem+'-render-preparation-audit.json').write_text(json.dumps(out,indent=2))
print(out['result']);print(json.dumps(out['rows'][:3],indent=2))
