"""Verify original material eligibility precedes first opponent allocation."""
import json, struct, sys
from pathlib import Path
report_path = Path(sys.argv[1])
report = json.loads(report_path.read_text())
slot_path = Path(report['model_pose_trace']).with_suffix('.slots.bin')
def rows(path, magic):
    raw = path.read_bytes()
    assert len(raw) % 32 == 0, 'Truncated trace'
    result = [struct.unpack_from('<8I', raw, at) for at in range(0, len(raw), 32)]
    assert all(row[0] == magic for row in result), 'Mixed trace records'
    return result
material = rows(Path(str(slot_path) + '.eligibility.bin'), 0x31454d4e)
slots = rows(slot_path, 0x31534c4e)
source = 33572092
pending = {}; pairs = []; boundary_posts = []
for row in material:
    key = (row[1], row[3])
    if row[2] == 0x030023b8:
        assert key not in pending
        pending[key] = row
    elif row[2] == 0x03002410:
        if key not in pending:
            assert row[3] != source, "Unpaired opponent material post"
            boundary_posts.append(row)
            continue
        entry = pending.pop(key)
        assert entry[5] == (entry[4] | 4) == row[4]
        assert entry[6] == row[6]
        pairs.append((entry, row))
    else:
        raise AssertionError('Unexpected material PC')
assert not any(key[1] == source for key in pending)
opponent = [pair for pair in pairs if pair[0][3] == source]
allocations = [row for row in slots if row[3] == source and row[2] == 0x080239ea]
assert opponent and allocations
entry, post = opponent[0]; allocation = allocations[0]
assert entry[1] == 13138 and entry[4:8] == (34, 38, 7, 255)
assert post[4] == 38
assert allocation[1] == 13139 and allocation[4:8] == (255, 13, 7, 38)
prior = [row for row in slots if row[3] == source and row[1] < allocation[1]]
assert prior and all(row[2] == 0x08023a16 and row[5] == 255 for row in prior)
evidence = dict(material_pairs=len(pairs), boundary_posts=boundary_posts, opponent_pairs=len(opponent), first_eligibility_refresh=entry[1], first_allocation_refresh=allocation[1], source=source, entry=entry, post=post, allocation=allocation, limitation='Original discrete appearance clocks only; fractional visibility and complete car motion integration remain unverified.')
report_path.with_suffix('.opponent-eligibility-clock.json').write_text(json.dumps(evidence, indent=2))
print('PASS', len(pairs), 'material pairs; opponent eligibility 13138 -> allocation 13139')
