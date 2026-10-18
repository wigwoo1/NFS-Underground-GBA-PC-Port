import json,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
rows=[]
for event in ledger['records']:
 prepared=event['prepared'];st=prepared['source_setup_ticks'];x=prepared['source_input_ticks']
 stamps=[st[0],*x,st[1]];assert stamps==sorted(stamps) and all(stamps)
 values=[(b-a)/1e6 for a,b in zip(stamps,stamps[1:])]
 assert sum(b-a for a,b in zip(stamps,stamps[1:]))==st[1]-st[0]
 rows.append(dict(identity=[event['epoch'],event['generation'],event['display_index']],gap_ms=event['interval_ns']/1e6,input_setup_ms=(st[1]-st[0])/1e6,partition_ms=dict(zip(['envelope','hud_row_validation','background_text_validation','hud_cache_and_copy','post_input'],values))))
out=dict(result='PASS_COMPLETE_SOURCE_INPUT_SUBSTAGE_PARTITION',rows=rows,scope='Every zero-drop native long-gap input stage partition sums exactly. Elapsed includes scheduling; cache-and-copy includes statistics and conditional memcmp/copy, not exclusive copy CPU.')
p.with_name(p.stem+'-source-input-partition.json').write_text(json.dumps(out,indent=2));print(out['result']);print(rows)
