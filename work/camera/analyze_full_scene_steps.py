"""Measure actual live full-frame steps, tagging source and membership changes.

RGB differences include legitimate motion, texture sampling and HUD updates.
They are measurements, never automatic proof of smoothness or a defect.
"""
from pathlib import Path
import csv, json, sys, ctypes as C, struct
import numpy as np
from PIL import Image
p=Path('work/camera');prefix=sys.argv[1]
source=list(csv.DictReader((p/(prefix+'-source-sources.csv')).open()))
packets=json.loads((p/(prefix+'-packet-tests.json')).read_text())['records']
replay=json.loads((p/(prefix+'-hud-replay-tests.json')).read_text())
assert replay['result']=='PASS' and replay['exact_live_frames']==12
assert len(source)==len(packets)==12
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
class Packet(C.Structure):_fields_=[('serial',C.c_uint),('begin',C.c_uint),('end',C.c_uint),('page',C.c_uint),('sections',Section*5)]
bridge=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()))
bridge.nf_scene_packet_view.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Packet)]
identities=[]
for i,metadata in enumerate(packets):
    data=(p/f'{prefix}-{i:03}.packet').read_bytes();owned=C.create_string_buffer(data);packet=Packet()
    assert bridge.nf_scene_packet_view(owned,len(data),C.byref(packet))
    section=packet.sections[4];raw=C.string_at(section.data,section.size)
    magic,count=struct.unpack_from('<II',raw)
    assert magic==0x3149464e and count==metadata['world_surfaces']+metadata['models']
    rows=[struct.unpack_from('<5I',raw,8+20*j) for j in range(count)]
    assert len(set(rows))==len(rows), 'Duplicate source identity tuple'
    identities.append(set(rows))
records=[];previous=np.asarray(Image.open(p/f'{prefix}-source-000.ppm')).copy()
for i in range(1,12):
    current=np.asarray(Image.open(p/f'{prefix}-source-{i:03}.ppm'))
    assert current.shape==previous.shape==(2160,3840,3)
    delta=np.abs(current.astype(np.int16)-previous.astype(np.int16))
    changed=np.any(delta,axis=2)
    a,b=source[i-1:i+1];dt=float(b['target'])-float(a['target']);assert dt>0
    pa,pb=packets[i-1:i+1]
    pair_changed=(a['older'],a['newer'])!=(b['older'],b['newer'])
    # Adjacent pairs share the boundary snapshot; don't silently bridge a gap.
    if pair_changed:assert a['newer']==b['older'], (i,a,b)
    membership=lambda r:[r[k] for k in ('road_surfaces','wall_surfaces','models')]
    records.append(dict(from_index=i-1,to_index=i,original_refresh_step=dt,
                        identity_rows_added=[list(x) for x in sorted(identities[i]-identities[i-1])],
                        identity_rows_removed=[list(x) for x in sorted(identities[i-1]-identities[i])],
                        source_pair_changed=pair_changed,hud_refresh_changed=a['hud_refresh']!=b['hud_refresh'],
                        membership_count_changed=membership(pa)!=membership(pb),before_counts=membership(pa),after_counts=membership(pb),
                        changed_pixels=int(changed.sum()),mean_absolute_channel_change=float(delta.mean()),
                        mean_absolute_change_per_original_refresh=float(delta.mean()/dt),
                        per_horizontal_quarter_changed_pixels=[int(chunk.sum()) for chunk in np.array_split(changed,4,axis=0)]))
    previous=current.copy()
report=dict(result='PASS',steps=11,source_pair_transitions=sum(r['source_pair_changed'] for r in records),
            membership_count_transitions=sum(r['membership_count_changed'] for r in records),records=records,
            scope='Temporal differences in twelve actual live 4K full frames independently verified by complete replay. Counts do not prove identity continuity; RGB changes conflate legitimate motion/HUD and discontinuity. No smooth60fps claim.')
(p/(prefix+'-full-scene-step-tests.json')).write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
