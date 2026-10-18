"""Analyze actual original-cycle evidence; never retime or repair scene packets."""
import argparse,csv,json,statistics
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("--capture",type=Path,required=True)
p.add_argument("--availability",type=Path)
p.add_argument("--output",type=Path,required=True)
a=p.parse_args()
capture=json.loads(a.capture.read_text());rows=capture["scene_timing"]
assert len(rows)>1 and len(rows)==len(capture["packets"])
def phase(r):
    until=r[11] if r[11]<2**63 else r[11]-2**64
    return ((r[9]-160)%228)*1232+(1232 if r[10]&2 else 1008)-until
errors=[]
for old,new in zip(rows,rows[1:]):
    assert old[0]==new[0] and old[1]+1==new[1] and old[3]==new[2]
    errors.append(new[4]-old[4]-(new[3]-old[3])*280896-phase(new)+phase(old))
assert set(errors)=={0}, "Video phase does not agree exactly with measured original cycle deltas"
def summary(v):
    return dict(min=min(v),median=statistics.median(v),max=max(v))
result=dict(result="PASS",scenes=len(rows),exact_cycle_phase_deltas=len(errors),
    cycle_phase_error_max=max(abs(v) for v in errors),
    flip_phase_frames=summary([phase(r)/280896 for r in rows]),
    last_geometry_to_flip_frames=summary([(r[4]-r[6])/280896 for r in rows]),
    last_camera_setup_to_flip_frames=summary([(r[4]-r[17])/280896 for r in rows]),
    last_geometry_addresses=sorted(set(hex(r[7]) for r in rows)),
    scope="Original scene timing diagnostics; no interpolation change or gameplay pacing claim")
if a.availability:
    samples=list(csv.DictReader(a.availability.open()))
    after=[r for r in samples if int(r["status"])==3 and int(r["timing_valid"])]
    warm=[r for r in after if float(r["elapsed"])>=2]
    def classify(v):
        covered=[r for r in v if float(r["target"])<=int(r["latest_packet_end"])+float(r["flip_phase"])]
        return dict(after_requests=len(v),within_precise_latest_flip=len(covered),
                    beyond_precise_latest_flip=len(v)-len(covered),
                    examples=[dict(elapsed=float(r["elapsed"]),target=float(r["target"]),
                        latest_end=int(r["latest_packet_end"]),flip_phase=float(r["flip_phase"]),
                        precise_latest_flip=int(r["latest_packet_end"])+float(r["flip_phase"]),
                        within_precise_latest_flip=r in covered) for r in v])
    result["live_all"]=classify(after);result["live_warm"]=classify(warm)
    result["interpretation"]="Precise flip coverage alone is not a valid pose timestamp or a rendered fix. Original logic/camera sample ownership still needs recovery."
a.output.write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
