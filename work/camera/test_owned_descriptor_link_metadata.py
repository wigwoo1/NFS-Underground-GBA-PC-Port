"""Actual snapshot metadata and private synthetic link ownership checks."""
import json,struct,hashlib
from pathlib import Path
from dataclasses import replace
from owned_graph_packet import GraphPacket
base=Path('outputs/nfsug-native-renderer/camera-research/checkpoints')
fixture=base/'live-source-context-20261007/failure-snapshot';results=[]
for path in sorted(fixture.glob('*.graph.bin')):
 g=GraphPacket.decode(path.read_bytes());links=g.descriptor_links
 assert set(links)==set(g.graph()[0]) and all(v==65535 for v in links.values())
 assert g.descriptor_links is links
 try:links[g.root]=0
 except TypeError:pass
 else:raise AssertionError('Mutable descriptor metadata')
 ring=bytearray(g.geometry);first=struct.unpack_from('<I',ring)[0];target=next(k for k in links if k!=first)
 struct.pack_into('<H',ring,48,target);synthetic=replace(g,geometry=ring)
 assert synthetic.descriptor_links[first]==target and g.descriptor_links[first]==65535
 ring[48:50]=struct.pack('<H',511);missing=replace(g,geometry=ring)
 try:missing.descriptor_links
 except ValueError as e:assert str(e)=='Incomplete linked graph ownership'
 else:raise AssertionError('Unowned linked target accepted')
 results.append(dict(file=path.name,descriptors=len(links),synthetic_source=first,synthetic_target=target,immutable=True,missing_target_rejected=True))
h=json.loads((base/'native-committed-sample-20261006/protected-hashes.json').read_text());assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest().upper()==v for k,v in h.items())
cp=base/'owned-link-metadata-20261007';cp.mkdir(exist_ok=True)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=results,protected_assets='PASS',scope='Actual snapshot descriptor metadata plus private synthetic ownership; no live linked scene claim'),indent=2))
(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());(cp/'owned_graph_packet.py').write_bytes(Path('work/camera/owned_graph_packet.py').read_bytes());print(json.dumps(results))
