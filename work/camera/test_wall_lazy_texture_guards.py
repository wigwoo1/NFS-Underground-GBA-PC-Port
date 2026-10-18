import struct,json,gc
from types import SimpleNamespace
from pathlib import Path
from owned_graph_wall_sources import wall_sources as original
from owned_wall_lazy_texture_candidate import wall_sources as candidate,TextureSpan

def material(identifier,mode,alias,pixels):
 h=[0]*12;h[3]=identifier;h[5]=2;h[6]=8;h[7]=123;h[8]=len(pixels);h[9]=mode;h[10]=alias
 return struct.pack('<12I',*h)+bytes(range(72))+(pixels if mode==1 else b'')
def geometry(identifier,mi):
 vertex=bytearray(68);struct.pack_into('<H',vertex,44,mi)
 return struct.pack('<4I',identifier,1,0,0)+bytes(48)+bytes(vertex)
def graph(materials):return SimpleNamespace(materials=materials,geometry=geometry(1,1)+geometry(2,2),offsets=bytes(64),validate=lambda:None)
checks=[]
for kind in (bytes,bytearray):
 g=graph(material(1,1,7,b'first')+material(2,2,7,b'first'));g.materials=kind(g.materials);g.geometry=kind(g.geometry);g.offsets=kind(g.offsets)
 for descriptors in (None,set(),{1},{2}):
  a=original(g,descriptors=descriptors);cache=[g,None];b=candidate(g,descriptors=descriptors,material_cache=cache);assert a==b
  allrows=candidate(g,material_cache=cache);assert allrows==original(g)
  assert allrows[0].texture is allrows[1].texture
  if kind is bytearray:assert not any(isinstance(v[2],TextureSpan) for v in cache[1].values())
  retained=allrows;del cache;gc.collect();assert retained[0].texture==b'first'
  checks.append(dict(kind=kind.__name__,descriptors=None if descriptors is None else sorted(descriptors)))
# Original alias lookup failure remains even when its descriptor is unrequested.
g=graph(material(1,1,7,b'first')+material(2,2,99,b'first'))
errors=[]
for f in (original,candidate):
 try:f(g,descriptors={1})
 except KeyError as e:errors.append(e.args)
 else:raise AssertionError('Dangling alias accepted')
assert errors[0]==errors[1]
# Shared alias redefinition preserves earlier material spans and later lookup semantics.
g=graph(material(1,1,7,b'first')+material(3,1,7,b'later')+material(2,2,7,b'later'))
a=original(g);b=candidate(g);assert a==b and b[0].texture==b'first' and b[1].texture==b'later'
# Cache authority guard unchanged.
for f in (original,candidate):
 try:f(g,material_cache=[object(),None])
 except ValueError:pass
 else:raise AssertionError('Wrong cache owner accepted')
out=dict(result='PASS_LAZY_TEXTURE_ALIAS_MUTABLE_GUARDS',cases=checks,dangling_alias_errors=errors,alias_redefinition=True,cache_owner_guard=True,scope='Synthetic alias/copy/owner edge checks; original graph validation remains authoritative')
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-lazy-textures-20261010');(p/'guards.json').write_text(json.dumps(out,indent=2));print(out['result'])
