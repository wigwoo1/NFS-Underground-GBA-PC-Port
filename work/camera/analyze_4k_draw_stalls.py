import json,sys,collections
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());st=json.loads(Path(sys.argv[2]).read_text());samples={x['display_index']:x for x in r['presentation_samples'] if x.get('queued_draw_stage_profile')};rows=[];counts=collections.Counter()
for gap in st['largest']:
 s=samples[gap['display_index']];p=s['queued_draw_stage_profile'];parts=dict(input_keyboard=p[0]/1e6,input_controller=p[1]/1e6,input_publication=p[2]/1e6,input_remainder=p[3]/1e6,background_sky=p[4]/1e6,world=p[5]/1e6,hud=p[6]/1e6)
 dominant=max(parts,key=parts.get);counts[dominant]+=1
 rows.append(dict(display_index=s['display_index'],gap_ms=gap['gap_ms'],draw_ms=(s['draw_complete_ns']-s['sample_begin_ns'])/1e6,dominant=dominant,parts=parts,hud_prolog_ms=p[7]/1e6,hud_candidate_prepare_ms=p[8]/1e6,hud_compose_restore_ms=p[9]/1e6))
out=dict(result='RECORDED_DRAW_SUBSTAGES',dominant_counts=dict(counts),rows=rows,scope='Captured native wall durations include scheduling/driver waits; input field interpretation follows native target probe. Not exclusive CPU/GPU cause.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(dict(dominant_counts=dict(counts),worst=rows[:4]))

