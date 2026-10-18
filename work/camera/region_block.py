"""Captured-call shape validation, not sampled road eligibility."""
def region_block(record, commands, origins, wall_passes):
    begin,end=record[6:8]
    if not 0<=begin<=end<=len(commands):raise ValueError('invalid interval')
    prefix=[];roads=[];suffix=[];phase=0
    for index in range(begin,end):
        command=commands[index];origin=origins[index]
        if command[0]==3 or command[5] or origin is None or tuple(origin[2:6])!=tuple(record[:4]):
            raise ValueError('nested or object command')
        if command[0]==1:
            if phase>1 or roads:raise ValueError('multiple or misplaced roads')
            roads.append(index);phase=1
        elif command[0]==2:
            if wall_passes[index] is None:raise ValueError('missing wall phase')
            if wall_passes[index][1]:suffix.append(index);phase=2
            else:
                if phase:raise ValueError('wall prefix after road or suffix')
                prefix.append(index)
        else:raise ValueError('unsupported command')
    return dict(begin=begin,end=end,prefix=prefix,road=roads,suffix=suffix,
                prefix_tail=prefix[-1]+1 if prefix else begin,suffix_tail=end)
