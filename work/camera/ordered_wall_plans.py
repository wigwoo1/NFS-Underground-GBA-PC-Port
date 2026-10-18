"""Diagnostic assembly; unresolved entrants are never assigned invented order."""
def assemble(commands, plans, wall_passes=None, occurrences=False):
    """Occurrence mode requires scene-local captured_index on every wall plan.

    The caller must bind plans and commands to the same retained scene; these
    indices are not stable identities for interpolation across scenes.
    """
    if wall_passes is not None:
        if len(wall_passes) != len(commands):
            raise ValueError('pass metadata count')
        for command, entry in zip(commands, wall_passes):
            if command[0] != 2:
                if entry is not None: raise ValueError('pass on nonwall')
            elif (not entry or len(entry) != 3 or
                  (entry[0], bool(entry[1])) not in ((0x0300297c, False), (0x03002b38, True))):
                raise ValueError('unknown wall pass')
    slots = {}
    for index, command in enumerate(commands):
        if len(command) != 6 or command[0] not in (1, 2, 3):
            raise ValueError('invalid captured command')
        if command[0] == 2:
            key = index if occurrences else (command[2], bool(command[5]))
            if key in slots:
                raise ValueError('ambiguous repeated wall source')
            slots[key] = index
    if sum(c[0] == 3 for c in commands) != 1:
        raise ValueError('expected one model command')
    matched, pending = {}, []
    for plan in plans:
        key = plan.get('captured_index') if occurrences else (plan['source'], plan.get('object_dispatch') is not None)
        index = slots.get(key)
        if occurrences:
            if type(key) is not int or index is None:
                raise ValueError('invalid captured occurrence')
            command = commands[index]
            if (plan['source'] != command[2] or
                (plan.get('object_dispatch') is not None) != bool(command[5])):
                raise ValueError('occurrence surface mismatch')
        if index is None:
            pending.append(dict(plan))
        elif index in matched:
            raise ValueError('multiple plans target one captured command')
        else:
            if wall_passes is not None and plan['pass_id'] != int(bool(wall_passes[index][1])):
                raise ValueError('sampled wall changed captured pass')
            matched[index] = dict(plan)
    ordered = []
    for index, command in enumerate(commands):
        if command[0] != 2 or index in matched:
            ordered.append(dict(captured_index=index, command=list(command),
                                wall_plan=matched.get(index)))
    return dict(commands=ordered, pending_insertion=pending,
                complete=not pending)

def assemble_anchored(commands, plans, wall_passes=None):
    """Insert first-pass entrants only into an unchanged, contiguous region run.

    Native first-pass edges traverse increasing source addresses. Require a
    later retained edge anchor; unanchored regions and deferred passes wait.
    This does not recompute object/model order or road visibility.
    """
    result = assemble(commands, plans, wall_passes)
    pending = []
    for entrant in sorted(result['pending_insertion'], key=lambda p:p['source']):
        peers = [x for x in result['commands'] if x['wall_plan'] is not None
                 and x['wall_plan']['region'] == entrant['region']
                 and x['wall_plan'].get('object_dispatch') is None]
        positions = [result['commands'].index(x) for x in peers]
        sources = [x['wall_plan']['source'] for x in peers]
        valid = (entrant.get('object_dispatch') is None and entrant['pass_id'] == 0
                 and peers and all(x['wall_plan']['pass_id'] == 0 for x in peers)
                 and all(x['wall_plan']['queue_index'] == entrant['queue_index'] for x in peers)
                 and positions == list(range(positions[0], positions[-1]+1))
                 and sources == sorted(set(sources))
                 and len({x['command'][4] for x in peers}) == 1)
        anchor = next((x for x in peers if x['wall_plan']['source'] > entrant['source']), None)
        if not valid or anchor is None:
            pending.append(entrant)
            continue
        descriptor = anchor['command'][4]
        result['commands'].insert(result['commands'].index(anchor), dict(
            captured_index=None, command=[2, 0xffffffff, entrant['source'], 0, descriptor, 0],
            wall_plan=entrant, insertion_basis='first-pass retained region anchor'))
    result['pending_insertion'] = pending
    result['complete'] = not pending
    return result
