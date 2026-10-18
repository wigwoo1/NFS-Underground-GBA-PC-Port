import struct,json,weakref,gc
from pathlib import Path
from owned_active_batch_publication import ActiveBatchPublication
class Owner:pass
book=ActiveBatchPublication();owner=Owner();weak=weakref.ref(owner)
rows=[dict(epoch=7,generation=1,source_older=10,refresh=14,display_index=20+i,alpha=(i+1)/4) for i in range(3)]
token=book.begin(7,1,rows,owner);del owner;gc.collect();assert weak() is not None
bits=struct.unpack('<Q',struct.pack('<d',.25))[0];sample=[7,1,10,14,20,bits,12345,1]
assert book.snapshot(sample,1,7,1)['pending_indices']==[21,22]
bad=list(sample);bad[4]=22
try:book.finish(token,[bad])
except ValueError:pass
else:raise AssertionError('Bad prefix published')
assert not book.published and book.active is not None
out=book.finish(token,[sample]);assert len(out)==1 and book.last['display_index']==20
assert book.snapshot(sample,1,7,3)['pending_indices']==[]
gc.collect();assert weak() is None
suffix=[dict(r,generation=3) for r in rows[1:]];next_token=book.begin(7,3,suffix,Owner());assert book.snapshot(sample,1,7,3)['pending_indices']==[21,22]
try:book.finish(token,[])
except ValueError:pass
else:raise AssertionError('Stale token accepted')
book.finish(next_token,[]);assert book.last['display_index']==20 and book.active is None
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/active-batch-publication-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',owner_retained_until_publication=True,atomic_bad_prefix_rejection=True,canceled_suffix_pending=[21,22],scope='Publication ownership/bookkeeping component; native concurrent snapshot tests separately verified. No live integration proof.'),indent=2));print('PASS active batch lifetime, atomic prefix publication and canceled suffix')
