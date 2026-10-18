"""Immutable original matrix-builder inputs, keyed by source and scratch address."""
from dataclasses import dataclass
from types import MappingProxyType
import struct

@dataclass(frozen=True)
class BuilderInputs:
    refresh: int
    camera_address: int
    object_address: int
    matrix_address: int
    source: bytes
    camera: bytes
    initial_matrix: bytes
    external_enabled: int | None = None
    external_matrix: bytes | None = None

class OwnedModelBuilders:
    def __init__(self, payload):
        payload = bytes(payload)
        self.payload = payload
        by_key = {}
        previous = -1
        at = 0
        while at < len(payload):
            if len(payload)-at < 32: raise ValueError("Truncated builder header")
            h = struct.unpack_from('<8I', payload, at)
            if h[0] != 0x31424d4e or (h[5],h[7]) not in ((260,0),(300,2)) or h[6] != 1:
                raise ValueError('Invalid builder inputs header')
            stride = 32+h[5]
            if len(payload)-at < stride: raise ValueError("Truncated builder inputs")
            if h[1] < previous:
                raise ValueError('Builder inputs cross a refresh reset')
            previous = h[1]
            value = BuilderInputs(h[1], h[2], h[3], h[4],
                payload[at+32:at+196], payload[at+196:at+244], payload[at+244:at+292],
                struct.unpack_from("<I",payload,at+292)[0] if h[7]==2 else None,
                payload[at+296:at+332] if h[7]==2 else None)
            by_key.setdefault((h[3], h[4]), []).append(value)
            at += stride
        self.records = MappingProxyType({key: tuple(values) for key, values in by_key.items()})

    def at(self, object_address, matrix_address, refresh):
        values = self.records.get((object_address, matrix_address), ())
        # Last invocation wins, including multiple builders within one refresh.
        for value in reversed(values):
            if value.refresh <= refresh:
                return value
        raise ValueError('No owned builder before consumed transform')
