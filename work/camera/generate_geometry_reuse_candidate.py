from pathlib import Path
p=Path('work/camera');s=(p/'native_geometry_sources_sky_candidate.c').read_text()
a='unsigned slot=refresh%16;free(frames[slot].data);frames[slot]=building;frames[slot].refresh=refresh;frames[slot].valid=!building.failed;'
b='unsigned slot=refresh%16;Geometry reusable=frames[slot];frames[slot]=building;frames[slot].refresh=refresh;frames[slot].valid=!building.failed;'
assert s.count(a)==1;s=s.replace(a,b)
a='memset(&building,0,sizeof(building));return valid;'
b='building=reusable;building.size=0;building.refresh=0;building.valid=0;building.failed=0;return valid;'
assert s.count(a)==1;s=s.replace(a,b)
(p/'native_geometry_reuse_candidate.c').write_text(s)
