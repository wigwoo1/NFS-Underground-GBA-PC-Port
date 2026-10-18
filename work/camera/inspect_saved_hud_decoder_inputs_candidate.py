import sys,json,ctypes as C,struct
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
exec(compile(Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0],'saved-scene','exec'))

size=34944
pairs=[]
for frame in frames:
 h=struct.unpack_from('<6I2Q',frame);pairs.append([frame[40+h[2]+y*size:40+h[2]+(y+1)*size] for y in range(160)])
parts={'registers':(8,104),'affine':(104,128),'obj_vram':(128,32896),'palette':(32896,33920),'oam':(33920,34944)}
out={k:sum(a[lo:hi]!=b[lo:hi] for a,b in zip(*pairs)) for k,(lo,hi) in parts.items()}
keys=lambda row: row[8:10]+row[72:84]+row[88:90]+row[92:94]+row[128:]
out['rows_with_changed_decoder_inputs']=sum(keys(a)!=keys(b) for a,b in zip(*pairs))

d=C.CDLL(str(Path('work/camera/owned-hud-row-decode-cache-candidate.dll').resolve()));d.nf_hud_row_decode_direct.argtypes=[C.c_void_p,C.c_void_p]
changed_outputs=[]
for y,(a,b) in enumerate(zip(*pairs)):
 first=C.create_string_buffer(2400);second=C.create_string_buffer(2400)
 assert d.nf_hud_row_decode_direct(C.create_string_buffer(a),first)==1
 assert d.nf_hud_row_decode_direct(C.create_string_buffer(b),second)==1
 if first.raw!=second.raw:changed_outputs.append(y)
out['decoder_output_changed_rows']=changed_outputs
out['changed_oam_entries']= [i for i in range(128) if pairs[0][0][33920+i*8:33928+i*8]!=pairs[1][0][33920+i*8:33928+i*8]]
out['result']='PASS_SAVED_HUD_INPUT_OUTPUT_CHANGE_AUDIT'
out['scope']='Two actual saved endpoints; exact fields and all native scanline outputs compared. Identical outputs do not establish safe reuse when decoder inputs change; no wider scene or performance claim.'
Path('work/camera/prototype-runs/saved-hud-input-output-changes-20261009.json').write_text(json.dumps(out,indent=2));print(out);history.close()
