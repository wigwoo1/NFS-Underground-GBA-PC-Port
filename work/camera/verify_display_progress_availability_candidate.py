"""Reject non-progressing display reports before any cadence conclusion."""
import json,sys
from pathlib import Path
def assess(report):
 p=report['dxgi_display_progress'];raw=report.get('dxgi_raw_diagnostics',{})
 valid=p['observed_advances']>0 and p['reported_image_advance']>0 and p['reported_refresh_advance']>0 and p['excess_refresh_spans_dropped']==0
 return dict(result='DISPLAY_PROGRESS_OBSERVED' if valid else 'DISPLAY_CADENCE_UNVERIFIABLE',queries=p['queries'],observed_advances=p['observed_advances'],present_status_counts=raw.get('present_status_counts'),reason=None if valid else 'No advancing display evidence or incomplete span journal; empty excess spans are not a pass.',scope='Availability gate only; does not certify pixels or whole-scene60fps.')
if __name__=='__main__':
 r=json.loads(Path(sys.argv[1]).read_text());out=assess(r)
 if len(sys.argv)>2:Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
 print(json.dumps(out,indent=2))
