import struct,json
from pathlib import Path
from owned_batch_commit_snapshot import resolve_pause_snapshot
bits=struct.unpack('<Q',struct.pack('<d',.5))[0];sample=[7,1,10,14,20,bits,12345,1]
published=dict(source_older=10,refresh=14,display_index=20,alpha=.5,generation=1)
rows=[dict(epoch=7,generation=3,source_older=14,refresh=18,display_index=i,alpha=.5) for i in (21,22)]
a=resolve_pause_snapshot(sample,1,7,3,rows,published);assert a['pending_indices']==[21,22] and a['unpublished_committed_indices']==[]
b=resolve_pause_snapshot([0]*8,0,7,1,[dict(rows[0],generation=1)],None);assert b['last_committed'] is None and b['pending_indices']==[21]
assert resolve_pause_snapshot(sample,1,7,3,(),published)['last_committed']['display_index']==20
cases=[('missing_native',lambda:resolve_pause_snapshot([0]*8,0,7,3,rows,published)),('missing_python',lambda:resolve_pause_snapshot(sample,1,7,3,rows,None)),('gap',lambda:resolve_pause_snapshot(sample,1,7,3,[dict(rows[0],display_index=22)],published)),('retired',lambda:resolve_pause_snapshot(sample,1,7,4,rows,published)),('wrong_epoch',lambda:resolve_pause_snapshot(sample,1,8,3,(),published))]
for name,fn in cases:
 try:fn()
 except ValueError:pass
 else:raise AssertionError(name)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/batch-pause-fallback-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',previous=a,startup=b,rejected=[x[0] for x in cases],scope='Snapshot bookkeeping component; actual native concurrent active-prefix test separately verified, no live integration proof.'),indent=2));print('PASS previous/startup/no-active snapshot fallback and5rejections')
