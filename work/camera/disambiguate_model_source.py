from pathlib import Path
p=Path('work/camera/owned_model_record_owners.py');s=p.read_text();needle="   if len(matches)!=1:raise ValueError('Ambiguous or missing source model record owner')";assert needle in s
code='''   if len(matches)>1:
    import struct
    from owned_scenery_projection import SceneryProjection
    owned_scene=pair.portal.motion.scene_pair[endpoint] if pair.portal.motion.scene_pair else None
    if owned_scene is None or owned_scene.builders is None:raise ValueError('Missing duplicate model builder ownership')
    state=scene.graph.context[:256];base=struct.unpack_from('<I',state,60)[0];matrix_base=struct.unpack_from('<I',state,252)[0];projection=SceneryProjection(rom);exact=[]
    for owner in matches:
     visit=next(v for v in visits if v['object']==owner)
     if not 31<=visit['dispatch']['model']<=36:raise ValueError('Unverified duplicate model kind')
     builder=owned_scene.builders.at(base+owner*164,matrix_base+visit['source'][136]*48,scene.refresh)
     matrix=projection.matrix(builder.camera,builder.source,builder.initial_matrix)
     if matrix==bytes(row['blocks'][2]):exact.append(owner)
    matches=exact
'''
s=s.replace(needle,code+needle);p.write_text(s)
