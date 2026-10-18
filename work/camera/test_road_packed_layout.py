from pathlib import Path
import runpy,struct,json,ctypes as C
p=Path('work/camera');ns=runpy.run_path(str(p/'test_road_zero_index.py'));u=ns['u'];regs={k:ns[k] for k in ['UC_ARM_REG_R0','UC_ARM_REG_SP','UC_ARM_REG_LR','UC_ARM_REG_PC']}
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
record=next(s for c in json.loads((p/'road-clip-inputs-0.5-motion-spans.json').read_text())['cases'] for s in c.get('spans',[]) if s['routine']==0x030056d8);a=record['params'];pairs=1<<a[0];height=(a[2]>>16)+1;texture=rom[a[5]-0x08000000:a[5]-0x08000000+pairs*height*2]
helper=runpy.run_path(str(p/'test_road_texture_indices.py'));state=helper['state'];material=helper['material'];regions=helper['regions'];struct.pack_into('<I',state,0,0x02004000);struct.pack_into('<H',material,26,a[0]);struct.pack_into('<H',material,10,height*2);regions[0x02004000]=texture
out=C.c_void_p();w=C.c_uint32();h=C.c_uint32();assert helper['fn'](helper['read'],None,0x02000000,0x02001000,C.byref(out),C.byref(w),C.byref(h))
try:owned=C.string_at(out,w.value*h.value)
finally:helper['d'].nf_surface_free(out)
sample_pairs=(a[1]>>16)+1
assert sample_pairs*2==pairs and (w.value,h.value)==(pairs,height)
u.mem_write(0x02010000,texture);u.mem_write(0x03007098,struct.pack('<I',0))
for y in range(height):
 params=[a[0],a[1],a[2],0,0,0x02010000,0x06001000,sample_pairs,0,y<<16,1<<16,0,0,0,0,0]
 u.mem_write(0x02002000,struct.pack('<16I',*params));u.mem_write(0x06001000,b'\xa5'*pairs)
 for reg,val in [('UC_ARM_REG_R0',0x02002000),('UC_ARM_REG_SP',0x03007b00),('UC_ARM_REG_LR',0x03007c00)]:u.reg_write(regs[reg],val)
 u.emu_start(0x030056d8,0x03007c00,count=10000);assert u.reg_read(regs['UC_ARM_REG_PC'])==0x03007c00
 assert bytes(u.mem_read(0x06001000,pairs))==owned[y*pairs:(y+1)*pairs],y
report=dict(result='PASS',original_packed_rows=height,sampled_pairs_per_row=sample_pairs,packed_stride_pairs=pairs,original_index_bytes=len(owned),returned_dimensions=[w.value,h.value],different_adjacent_byte_pairs=sum(texture[i]!=texture[i+1] for i in range(0,len(texture),2)),different_row_half_bytes=sum(texture[y*pairs*2+x]!=texture[y*pairs*2+pairs+x] for y in range(height) for x in range(pairs)),scope='Owned first-half packed rows exactly reproduce original affine sampling domain of one real texture; u mask admits half the stride pairs. Wider material/mask and continuous UV verification pending.')
(p/'road-packed-layout-tests.json').write_text(json.dumps(report,indent=2));print(report)
