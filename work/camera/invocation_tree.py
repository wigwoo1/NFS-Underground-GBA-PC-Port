"""Preserve captured invocation nesting; no sampled child eligibility inference."""
def invocation_tree(records,command_count):
    stack=[];parents=[];children=[[] for _ in records]
    for index,row in enumerate(records):
        begin,end,depth=row[6:9]
        if not 0<=begin<=end<=command_count:raise ValueError('invalid command interval')
        while len(stack)>depth:stack.pop()
        if len(stack)!=depth:raise ValueError('missing parent depth')
        parent=stack[-1] if stack else None
        if parent is not None:
            p=records[parent]
            if begin<p[6] or end>p[7]:raise ValueError('child outside parent')
            if children[parent] and records[children[parent][-1]][7]>begin:raise ValueError('overlapping siblings')
            children[parent].append(index)
        elif parents:
            previous=next(i for i in range(index-1,-1,-1) if parents[i] is None)
            if records[previous][7]>begin:raise ValueError('overlapping roots')
        parents.append(parent);stack.append(index)
    return parents,children
