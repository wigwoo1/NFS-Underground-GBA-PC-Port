from pathlib import Path
import ctypes as C,json,sys
r=Path('work').resolve();results=[]
for name in ['stable/before.dll','nfsprobe.dll']:
 d=C.CDLL(str(r/name));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_scene.restype=C.c_void_p
 assert d.nf_init(b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba',b'');assert d.nf_state(str(r/'driving.state').encode(),0);d.nf_scene_enable(1)
 overlay=(C.c_uint32*(240*160))();rows=[]
 for i in range(600):
  d.nf_frame(1);n=C.c_int();d.nf_scene(C.byref(n));d.nf_overlay(overlay);rows.append({'frame':i,'polygons':n.value,'opaque_overlay':sum(bool(v)for v in overlay)})
 results.append({'dll':name,'frames_without_geometry_after_warmup':sum(x['polygons']==0 for x in rows[12:]),'overlay_min':min(x['opaque_overlay']for x in rows[12:]),'overlay_max':max(x['opaque_overlay']for x in rows[12:]),'rows':rows});d.nf_close()
(r/'stable/scanout-tests.json').write_text(json.dumps(results,indent=2));print([{k:v for k,v in x.items()if k!='rows'} for x in results])
