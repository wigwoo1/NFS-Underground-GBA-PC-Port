"""Canonical 64-bit source-pixel identity used by capture and pack tools."""
import struct

def source_hash(rgba: bytes, width: int, height: int) -> int:
    value = 14695981039346656037
    for byte in struct.pack("<II", width, height) + rgba:
        value = ((value ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return value
