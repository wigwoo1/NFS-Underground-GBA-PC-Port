"""Scene-local reuse of successful immutable road material decoding."""
import inspect,textwrap
import owned_complete_road_candidates as base
original=base.road_candidates
source=textwrap.dedent(inspect.getsource(original))
source=source.replace('out=[];texture_cache={};at=offset=0','out=[];texture_cache={};decoded_materials={};at=offset=0')
a=source.index('   material,animation,texture=materials.get');b=source.index("   if texture is None:missing.append('texture')",a)
block=source[a:b]
replacement="   if mi in decoded_materials:\n    material,animation,texture=decoded_materials[mi]\n   else:\n"+'\n'.join(' '+line for line in block.splitlines())+"\n    if material is not None and texture is not None:decoded_materials[mi]=(material,animation,texture)\n"
source=source[:a]+replacement+source[b:]
ns=dict(original.__globals__);exec(compile(source,'scene-local-road-material-decode','exec'),ns)
candidate=ns['road_candidates']
