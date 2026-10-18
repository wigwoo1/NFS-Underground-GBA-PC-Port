"""Wrap the C-parity source-road mesh fixtures in retained historical scene layers."""
from pathlib import Path
import argparse,struct,json,hashlib
p=argparse.ArgumentParser()
for n in ('bundle','mesh_fixtures','output'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);base=a.bundle.read_bytes();chunks=[]
for i in range(4):at,size=struct.unpack_from('<QQ',base,64+i*16);chunks.append(base[at:at+size])
manifest={}
for mode in (9,10):
 for shape in (0,1):
  name=f'mode{mode}-shape{shape}-reverse0.nsp';original=(a.mesh_fixtures/name).read_bytes();geometry=bytearray(original);geometry[:32]=chunks[0][:32];struct.pack_into('<I',geometry,8,len(geometry));bundle=bytearray(base[:128])
  for i,chunk in enumerate([geometry]+chunks[1:]):struct.pack_into('<QQ',bundle,64+i*16,len(bundle),len(chunk));bundle+=chunk
  struct.pack_into('<Q',bundle,16,len(bundle));output=f'mode{mode}-shape{shape}.nab';(a.output/output).write_bytes(bundle);manifest[output]={'sha256':hashlib.sha256(bundle).hexdigest(),'c_parity_packet_sha256':hashlib.sha256(original).hexdigest(),'geometry_sections_identical_to_c_parity_fixture':geometry[32:]==original[32:],'synthetic_geometry_and_attributes':True,'retained_historical_layers':True,'expected_near_crossing_edges':2 if shape==0 else 0,'source_mode':mode}
(a.output/'fixture-manifest.json').write_text(json.dumps(manifest,indent=2));print('Prepared4 C-parity geometry GPU fixtures')
