"""Test review-only annotations for timed and legacy merged captures."""
import csv, json, sys, tempfile
from pathlib import Path
from PIL import Image

here=Path(__file__).resolve().parent
mod=here/"v2"
if not mod.is_dir(): mod=here.parent/"v2"
if not mod.is_dir(): mod=here
sys.path.insert(0,str(mod))
from audit_texture_sequences import audit
from build_texture_pack import source_hash
from merge_texture_sources import merge

def make_capture(folder, items, timed=True):
    folder.mkdir()
    textures=[]
    for item in items:
        image,serial=item[:2]
        stride,shade=item[2] if len(item)>2 else (4,1)
        key=f"{source_hash(image.tobytes(),image.width,image.height):016x}"
        name=key+".png"; image.save(folder/name)
        row={"hash":key,"width":image.width,"height":image.height,
             "address":0x0200D154,"kind":2,"source":name}
        if timed:
            row["first_seen_process_id"]=1234
            row["first_seen_draw_serial"]=serial
        row["stride"]=stride; row["shade"]=shade
        textures.append(row)
    (folder/"inventory.json").write_text(json.dumps({
        "format":"NFSUG-SOURCE-TEXTURE-INVENTORY-1","complete":False,
        "coverage":"fixture","texture_count":len(textures),"textures":textures
    }),encoding="utf-8")
    return folder

with tempfile.TemporaryDirectory(prefix="nfsug-sequence-audit-test-") as temp:
    root=Path(temp)
    base=Image.new("RGBA",(4,4),(80,80,80,255))
    early=base.copy(); early.putpixel((0,0),(10,10,10,255))
    dynamic=base.copy(); dynamic.putpixel((1,1),(90,80,80,255))
    alternate=base.copy(); alternate.putpixel((2,2),(120,80,80,255))
    cap=make_capture(root/"timed",[(early,1),(base,5),(dynamic,10),(alternate,10,(8,2))])
    merged=root/"merged"; merge([cap],merged)
    report=root/"sequence.csv"
    summary=audit(merged,report,5,(1,1,3,3))
    rows={r["hash"]:r for r in csv.DictReader(report.open(newline="",encoding="utf-8"))}
    key=lambda image:f"{source_hash(image.tobytes(),4,4):016x}"
    assert summary["timed_groups"]==2 and summary["timed_rows"]==4
    assert summary["pre_settle_outside_focus_candidates"]==1
    assert rows[key(early)]["review_flag"]=="review-pre-settle-outside-focus"
    assert rows[key(early)]["changed_outside_focus"]=="1"
    assert rows[key(base)]["review_flag"]=="settle-reference"
    assert rows[key(dynamic)]["review_flag"]=="post-settle-variant"
    assert rows[key(dynamic)]["changed_outside_focus"]=="0"
    assert rows[key(dynamic)]["stride"]=="4" and rows[key(dynamic)]["shade"]=="1"
    assert rows[key(alternate)]["stride"]=="8" and rows[key(alternate)]["shade"]=="2"
    try: audit(merged,report,5,(1,1,3,3))
    except FileExistsError: pass
    else: raise AssertionError("audit must not overwrite a prior report")

    legacy=make_capture(root/"legacy",[(base,0)],timed=False)
    legacy_merged=root/"legacy-merged"; merge([legacy],legacy_merged)
    legacy_report=root/"legacy.csv"
    legacy_summary=audit(legacy_merged,legacy_report,5,(1,1,3,3))
    legacy_rows=list(csv.DictReader(legacy_report.open(newline="",encoding="utf-8")))
    assert legacy_summary["legacy_rows"]==1
    assert legacy_rows[0]["review_flag"]=="no-draw-provenance"

print("PASS: transient candidates are annotated, settled variants retained, legacy rows preserved")
