"""Byte-exact equivalence tests for mutable owned-frame sky attachment."""
import ctypes as C
import struct
from types import SimpleNamespace

from owned_closed_graph import ClosedGraph
from owned_sky_frame import SKY_COVERAGE, attach_sky, attach_sky_inplace


class Boundary:
    def __init__(self, indices):
        self.indices = indices


class Sky:
    def __init__(self, indices):
        self.boundary = Boundary(indices)
        self.asset = self

    def match_graph(self, _graph):
        pass

    def verify(self, _boundary):
        pass


class Scene:
    identity = (7, 11)
    graph = object()

    def __init__(self, indices):
        self.sky = Sky(indices)


def make_frame(coverage_mode, indices):
    size = 40 + 2 * 76800
    data = bytearray(size)
    struct.pack_into("<6I2Q", data, 0, 0x3346474E, 11, 0, 0, 76800, 76800, 7, 11 * 280896)
    plane = 40
    sky_begin = plane + 10560
    coverage_begin = plane + 38400 + 10560
    data[sky_begin:sky_begin + 15136] = indices
    if coverage_mode == "all_owned":
        data[coverage_begin:coverage_begin + 15136] = SKY_COVERAGE
    elif coverage_mode == "mixed":
        data[coverage_begin:coverage_begin + 15136] = bytes(i & 1 for i in range(15136))
    elif coverage_mode == "invalid_coverage":
        data[coverage_begin + 17] = 2
    elif coverage_mode == "conflicting_index":
        data[coverage_begin] = 1
        data[sky_begin] ^= 0xFF
    elif coverage_mode != "unowned":
        raise ValueError(coverage_mode)
    return data


def verify_mode(mode):
    indices = bytes((i * 37 + 13) & 0xFF for i in range(15136))
    scene = Scene(indices)
    baseline = make_frame(mode, indices)
    expected = attach_sky(bytes(baseline), scene)
    for source in (bytearray(baseline), C.create_string_buffer(bytes(baseline))):
        actual = bytearray(source) if isinstance(source, bytearray) else source
        used = len(baseline)
        assert attach_sky_inplace(actual, scene, used) == used
        result = bytes(actual) if isinstance(actual, bytearray) else actual.raw[:used]
        assert result == expected, mode
    return len(expected)


def verify_rejection(mode):
    indices = bytes((i * 37 + 13) & 0xFF for i in range(15136))
    scene = Scene(indices)
    data = make_frame(mode, indices)
    before = bytes(data)
    try:
        attach_sky_inplace(data, scene, len(data))
    except ValueError:
        assert bytes(data) == before, "Rejected in-place attachment mutated its input"
    else:
        raise AssertionError(f"Expected {mode} to be rejected")


def main():
    sizes = {mode: verify_mode(mode) for mode in ("unowned", "all_owned", "mixed")}
    for mode in ("invalid_coverage", "conflicting_index"):
        verify_rejection(mode)
    camera = bytes(range(48))
    blocks = [b"" for _ in range(12)]
    blocks[4] = camera
    source = struct.pack("<4I", 0x3147534E, 1, 99, 12) + b"".join(
        struct.pack("<I", len(block)) + block for block in blocks
    )
    packet = struct.pack("<6I2Q", 0x3346474E, 11, len(source), 0, 0, 0, 7, 11 * 280896) + source
    graph = ClosedGraph(7, 11, SimpleNamespace(context=bytes(256) + camera), b"", b"", b"")
    graph.match_frame(memoryview(packet))
    print({"result": "PASS", "modes": sizes, "rejections": 2, "buffers": ["bytearray", "ctypes"], "memoryview_graph_match": True})


if __name__ == "__main__":
    main()
