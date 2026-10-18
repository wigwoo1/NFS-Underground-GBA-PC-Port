"""Verify per-update admitted snapshots without inventing device provenance."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=r['inputs'];updates=r['original_update_samples'];assert rows and len(rows)==len(updates)==r['original_updates']
known=connected=0
for row,u in zip(rows,updates):
 s=row['control_snapshot'];assert s['keys']==row['keys'] and not s['paused'] and not s['quit'];assert row['refresh']==u['refresh'];assert row['control_snapshot_ns']<=u['started_ns']
 if 'controller_connected' in s:known+=1;connected+=bool(s['controller_connected'])
out=dict(result='PASS_ADMITTED_CONTROL_SNAPSHOTS',updates=len(rows),connection_status_available_updates=known,connected_updates=connected if known else None,scope='Snapshot/key/refresh/timestamp consistency; connection does not prove controller originated mixed keyboard/gamepad keys. Smoke input is synthetic. No physical controller certification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
