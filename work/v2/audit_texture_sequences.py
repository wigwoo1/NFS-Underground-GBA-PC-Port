"""Review timed texture captures; labels possible transients but never removes source rows."""
import argparse, csv, json
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageChops
from build_texture_pack import source_hash

FORMAT = "NFSUG-SOURCE-TEXTURE-INVENTORY-1"
FIELDS = ("set_id","capture_name","process_id","address_hex","width","height","kind",
          "hash","draw_serial","stride","shade","pre_settle","focus_applicable","reference_hash","changed_pixels",
          "changed_in_focus","changed_outside_focus","changed_bbox","review_flag")

def _mask(delta):
    r,g,b=delta.split()
    return ImageChops.lighter(ImageChops.lighter(r,g),b)

def _count(mask):
    return sum(mask.histogram()[1:])

def audit(inventory, output, settle_after=64, focus=(63,167,237,195)):
    inventory=Path(inventory).resolve(); output=Path(output).resolve()
    if output.exists(): raise FileExistsError(output)
    data=json.loads((inventory/"inventory.json").read_text(encoding="utf-8"))
    if data.get("format")!=FORMAT: raise ValueError("unsupported inventory")
    names={r.get("id"):r.get("name","") for r in data.get("capture_sets",[]) if isinstance(r,dict)}
    groups=defaultdict(list); legacy=[]; images={}
    for tex in data.get("textures",[]):
        key=tex["hash"]; path=(inventory/tex["source"]).resolve(); path.relative_to(inventory)
        with Image.open(path) as opened: image=opened.convert("RGBA")
        w,h=int(tex["width"]),int(tex["height"])
        if image.size!=(w,h): raise ValueError("dimension mismatch: "+key)
        if source_hash(image.tobytes(),w,h)!=int(key,16): raise ValueError("hash mismatch: "+key)
        images[key]=image
        for cap in tex.get("captures",[]):
            hp="first_seen_process_id" in cap; hs="first_seen_draw_serial" in cap
            if hp!=hs: raise ValueError("partial provenance: "+key)
            if not hp: legacy.append((tex,cap)); continue
            pid,serial=cap["first_seen_process_id"],cap["first_seen_draw_serial"]
            if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=0xffffffff for v in (pid,serial)):
                raise ValueError("invalid provenance: "+key)
            addr=int(cap.get("address",tex.get("address",0))); kind=int(cap.get("kind",tex.get("kind",0)))
            renderer_fields=("stride","shade")
            renderer_present=tuple(field in cap for field in renderer_fields)
            if any(renderer_present) and not all(renderer_present): raise ValueError("partial renderer metadata: "+key)
            stride=cap.get("stride",""); shade=cap.get("shade","")
            if all(renderer_present) and any(isinstance(cap[field],bool) or not isinstance(cap[field],int) or not 0<=cap[field]<=0xffffffff for field in renderer_fields):
                raise ValueError("invalid renderer metadata: "+key)
            groups[(cap.get("set_id",""),pid,addr,w,h,kind,stride,shade)].append((serial,key,tex,cap))
    rows=[]; outliers=0; missing_ref=0
    for g,entries in groups.items():
        sid,pid,addr,w,h,kind,stride,shade=g; entries.sort(key=lambda x:(x[0],x[1]))
        ref=next((x for x in entries if x[0]>=settle_after),None)
        if ref is None: ref=entries[-1]; missing_ref+=1
        l,t,r,b=focus
        focus_applies = 0 <= l < r <= w and 0 <= t < b <= h
        focus_box = focus if focus_applies else (0, 0, w, h)
        for serial,key,tex,cap in entries:
            mask=_mask(ImageChops.difference(images[ref[1]].convert("RGB"), images[key].convert("RGB")))
            total=_count(mask); inside=_count(mask.crop(focus_box)); outside=total-inside; pre=serial<settle_after
            if key==ref[1]: flag="settle-reference"
            elif pre and outside: flag="review-pre-settle-outside-focus"; outliers+=1
            elif pre: flag="review-pre-settle-region-local"
            else: flag="post-settle-variant"
            box=mask.getbbox()
            rows.append({"set_id":sid,"capture_name":names.get(sid,""),"process_id":pid,
                "address_hex":f"{addr:08x}","width":w,"height":h,"kind":kind,"hash":key,
                "draw_serial":serial,"stride":stride,"shade":shade,"pre_settle":str(pre).lower(),"focus_applicable":str(focus_applies).lower(),"reference_hash":ref[1],
                "changed_pixels":total,"changed_in_focus":inside,"changed_outside_focus":outside,
                "changed_bbox":"" if box is None else ",".join(map(str,box)),"review_flag":flag})
    for tex,cap in legacy:
        sid=cap.get("set_id",""); addr=int(cap.get("address",tex.get("address",0)))
        rows.append({"set_id":sid,"capture_name":names.get(sid,""),"process_id":"",
            "address_hex":f"{addr:08x}","width":tex["width"],"height":tex["height"],
            "kind":cap.get("kind",tex.get("kind","")),"hash":tex["hash"],"draw_serial":"",
            "stride":cap.get("stride",""),"shade":cap.get("shade",""),"pre_settle":"","focus_applicable":"","reference_hash":"","changed_pixels":"","changed_in_focus":"",
            "changed_outside_focus":"","changed_bbox":"","review_flag":"no-draw-provenance"})
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    return {"timed_groups":len(groups),"timed_rows":sum(len(v) for v in groups.values()),
            "legacy_rows":len(legacy),"pre_settle_outside_focus_candidates":outliers,
            "groups_without_post_settle_reference":missing_ref,"report":str(output)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("inventory",type=Path); p.add_argument("output",type=Path)
    p.add_argument("--settle-after",type=int,default=63)
    p.add_argument("--focus",default="63,167,237,195")
    a=p.parse_args()
    try:
        focus=tuple(int(v) for v in a.focus.split(","))
        if len(focus)!=4 or not 0<=a.settle_after<=0xffffffff: raise ValueError("invalid threshold/focus")
        print(json.dumps(audit(a.inventory,a.output,a.settle_after,focus),indent=2))
    except (OSError,KeyError,ValueError,json.JSONDecodeError) as e: p.error(str(e))

if __name__=="__main__": main()
