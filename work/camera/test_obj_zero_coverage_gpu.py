"""Actual HUD shader against CPU stack with independently toggled BG coverage."""
from pathlib import Path
import json, struct, subprocess
import numpy as np

p = Path('work/camera').resolve()
reports = []
for priority, semi, blend in (
    (0, False, 0), (3, False, 0),
    (0, False, 0x1454), (3, False, 0x1454),
    (0, True, 0x400), (3, True, 0x400),
    (0, True, 0x2000), (3, True, 0x2000),
):
    row = bytearray(100480)
    struct.pack_into('<H', row, 8, 0x1044)
    struct.pack_into('<H', row, 8 + 0xc, 1)
    struct.pack_into('<H', row, 8 + 0x50, blend)
    struct.pack_into('<H', row, 8 + 0x52, 0x808)
    struct.pack_into('<H', row, 98432, 0x7c00)  # blue backdrop
    struct.pack_into('<H', row, 98432 + 514, 31)  # red OBJ
    for i in range(128):
        struct.pack_into('<H', row, 99456 + i * 8, 0x200)
    struct.pack_into('<3H', row, 99456, 32 | (0x400 if semi else 0),
                     32, 512 | (priority << 10))
    row[128 + 0x14000:128 + 0x14020] = bytes([0x11]) * 32
    source = p / 'obj-zero-coverage.bin'
    target, reference = p / 'obj-zero-coverage.rgba', p / 'obj-zero-coverage-cpu.rgba'
    source.write_bytes(row)
    subprocess.check_output([str(p / 'obj-candidate-gpu.exe'), str(source),
                             str(target), str(reference), '--zero-coverage'])
    actual = np.fromfile(target, np.uint32).reshape(2160, 3840)[::-1]
    expected = np.fromfile(reference, np.uint32).reshape(2160, 3840)
    different = actual != expected
    assert not different.any(), (priority, semi, hex(blend),
                                 int(different.sum()), np.argwhere(different)[:8].tolist())
    # Uncovered background must choose the blue backdrop outside sprites,
    # despite nonzero RGB deliberately retained in the alpha-zero texture.
    assert int(actual[2159, 0]) == 0xffff0000
    reports.append(dict(priority=priority, semi=semi, blend=blend,
                        exact_rgba_pixels=actual.size))
result = dict(result='PASS', cases=reports,
              scope='Actual candidate GPU shader: alternating alpha-zero/nonzero BG coverage, OBJ front/behind, ordinary alpha and semi OBJ BG/backdrop second targets. Component test; windows/brightness and live scene parity not established.')
(p / 'obj-zero-coverage-gpu-tests.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result))

