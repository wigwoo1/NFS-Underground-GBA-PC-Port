"""Check original ARM caller evidence without a disassembler dependency."""
from pathlib import Path
import json, struct
root = Path('work/camera')
ram = (root/'visibility-overflow-171-wide/iwram.bin').read_bytes()
def word(address):
    return struct.unpack_from('<I', ram, address-0x03000000)[0]
calls = []
for address in range(0x03001800, 0x030032f0, 4):
    value = word(address)
    if value >> 24 != 0xeb:
        continue
    displacement = value & 0xffffff
    if displacement & 0x800000:
        displacement -= 1 << 24
    if address + 8 + displacement*4 == 0x030032f0:
        calls.append(address)
assert calls == [0x03002a0c, 0x03002ab8], calls
for load, mask, store in [(0x030029e8,0x030029f8,0x030029fc),
                          (0x03002a98,0x03002aa4,0x03002aa8)]:
    assert word(load) == 0xe1d6c0ba  # ldrh ip,[r6,#10]
    assert word(mask) == 0xe20cc001  # and ip,ip,#1
    assert word(store) == 0xe58dc000 # str ip,[sp]
assert word(0x030027f8) == 0xe1a06001 # mov r6,r1, function entry
report = dict(result='PASS', call_sites=[hex(x) for x in calls],
    affine_argument='(read_u16(function_030027f0_argument_r1 + 10) & 1)',
    scope='Exact captured ARM instructions at both direct caller sites; structure ownership and correspondence to regenerated scene inputs remain unverified. No renderer behavior change.')
(root/'road-mode-caller-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
