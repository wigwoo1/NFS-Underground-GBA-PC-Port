from pathlib import Path
import json,sys
p=Path('work/camera');sys.path.insert(0,str(p.resolve()));sys.argv=['oracle','0.5','motion','road-full'];f=p/'test_sampled_object_dispatch.py';ns={'__name__':'diagnostic','__file__':str(f)}
try:exec(compile(f.read_text(),str(f),'exec'),ns)
except AssertionError:
 a,b=ns.get('assembled_packet'),ns.get('reference_packet');assert a is not None and b is not None
 offsets=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
 report=dict(result='PACKET_COMPARISON_MISMATCH',assembled_size=len(a),reference_size=len(b),different_bytes=len(offsets),first_offsets=offsets[:32],first_values=[dict(offset=i,assembled=a[i],reference=b[i]) for i in offsets[:12]],scope='Existing unchanged packet parity assertion failed; full asset checks preceding it passed. No gate relaxation.')
 (p/'packet-parity-diagnostic.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
else:
 a,b=ns['assembled_packet'],ns['reference_packet'];assert a==b
 report=dict(result='PASS_PACKET_PARITY',bytes=len(a),scope='Current fixture reference includes original ARM model clip; exact packet assertion passed.')
 (p/'packet-parity-diagnostic.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

