"""Lossless captured draw segmentation; child calls remain explicit barriers."""
from invocation_tree import invocation_tree

def scene_segments(records,commands,origins,wall_passes):
    if len(origins)!=len(commands) or len(wall_passes)!=len(commands):
        raise ValueError('command metadata length mismatch')
    parents,children=invocation_tree(records,len(commands))
    blocks=[]
    for index,row in enumerate(records):
        segments=[];cursor=row[6]
        def direct(begin,end):
            for slot in range(begin,end):
                command=commands[slot]
                if command[0]==3:kind='model'
                else:
                    if origins[slot] is None or tuple(origins[slot][2:6])!=tuple(row[:4]):
                        raise ValueError('direct command provenance mismatch')
                    if command[0]==1:kind='road'
                    elif command[0]==2:
                        if wall_passes[slot] is None:raise ValueError('missing wall phase')
                        kind='deferred' if wall_passes[slot][1] else 'wall'
                    else:raise ValueError('unknown command kind')
                if segments and kind in ('wall','deferred') and segments[-1]['kind']==kind and segments[-1]['end']==slot:
                    segments[-1]['end']=slot+1
                else:segments.append(dict(kind=kind,begin=slot,end=slot+1))
        for child in children[index]:
            direct(cursor,records[child][6])
            segments.append(dict(kind='child',begin=records[child][6],end=records[child][7],child=child))
            cursor=records[child][7]
        direct(cursor,row[7]);blocks.append(segments)
    return parents,blocks
