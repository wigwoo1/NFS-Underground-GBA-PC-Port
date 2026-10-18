"""Retain captured high-level drawing order without sorting by material."""
from surface_identity import wall_identity
def draw_order(scene):
    result=[];counts={'road':0,'wall':0,'model':0}
    for event in scene['events']:
        kind={0x030032f0:'road',0x03000304:'wall',0x03004770:'model'}.get(event['pc'])
        if kind is None or (kind=='model' and event['regs'][0]!=1):continue
        command={'kind':kind,'index':counts[kind],'event_id':event['id']}
        if kind=='wall':command['world_identity']=wall_identity(event)
        result.append(command)
        counts[kind]+=1
    return result,counts
