import json,sys
from pathlib import Path
src=Path(sys.argv[1]);r=json.loads(src.read_text());p=r['dxgi_display_progress'];successful=r['bounded_diagnostic_stats']['whole_run_sky_motion']['successful_samples'];assert p['queries']==successful and successful>0;assert p['excess_refresh_spans_dropped']==0
for span in p['excess_refresh_spans']:
 assert span['older_native_sample'] and span['newer_native_sample'] and span['qpc_frequency']>0
 assert span['end_qpc']>=span['start_qpc'] and span['refresh_advance']>span['image_advance']>0
windows=[x['presentation']['window'] for x in r['presentation_samples'] if x['native_result']==1];assert windows
out=dict(result='PASS_WHOLE_NATIVE_TRANSACTION_DISPLAY_OBSERVATION',successful_native_samples=successful,queries=p['queries'],progress=p,retained_client_sizes=sorted(set((x[3],x[4]) for x in windows)),desktop_monitors=r['dxgi_raw_diagnostics']['window_placement'][0]['monitors'],scope='Every successful native commit observed byverifiedtransactionhook; existingDXGIreportedprogress withgeneration/availabilityexclusions. Desktoppreview is640x480; native4Krender target differs fromdisplayresolution. No exactallpixelidentity orphysical4K60certification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],successful)
