"""Versioned external provenance keeps legacy exact fields and rejects truncation."""
import struct
from pathlib import Path
from owned_model_builder_inputs import OwnedModelBuilders
raw=Path('work/camera/prototype-runs/fullscene-failure-1791287389958948400/newer.builders.bin').read_bytes()
legacy=OwnedModelBuilders(raw);at=next(i for i in range(0,len(raw),292) if struct.unpack_from('<H',raw,i+42)[0]&32)
old=raw[at:at+292];h=list(struct.unpack_from('<8I',old));h[5]=300;h[7]=2
extra=struct.pack('<I9i',1,*range(9));new=struct.pack('<8I',*h)+old[32:]+extra
store=OwnedModelBuilders(new);value=store.at(h[3],h[4],h[1]);reference=legacy.at(h[3],h[4],h[1])
assert (value.source,value.camera,value.initial_matrix)==(reference.source,reference.camera,reference.initial_matrix)
assert value.external_enabled==1 and value.external_matrix==extra[4:]
assert isinstance(value.external_matrix,bytes)
for n in (1,31,32,291,292,331):
 try:OwnedModelBuilders(new[:n])
 except ValueError:pass
 else:raise AssertionError(('Accepted truncation',n))
assert reference.external_enabled is None and reference.external_matrix is None
print('PASS versioned external provenance, immutable payload, exact legacy fields and six truncated packet rejections')
