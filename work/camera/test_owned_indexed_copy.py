"""Owned asset equals independently verified original copy; atomic guards."""
import ctypes as C,csv,json,hashlib,runpy,struct
from pathlib import Path
p=Path(__file__).resolve().parent
reference=runpy.run_path(str(p/'test_original_image_copy_abi.py'))
rom=reference['rom'];d=C.CDLL(str(p/'indexed-copy-test.dll'));P=C.c_void_p;U=C.c_uint32;Z=C.c_size_t
Read=C.CFUNCTYPE(C.c_int,P,U,P,Z)
d.nf_indexed_copy_create.argtypes=[Read,P,U,U,U,U,U,U,P,P]
d.nf_indexed_copy_view.argtypes=[P,Z,P,P,P,P]
d.nf_indexed_copy_free.argtypes=[P]
available=True
@Read
def read(ctx,address,out,size):
 if not available or address<0x08000000 or address-0x08000000+size>len(rom):return 0
 C.memmove(out,rom[address-0x08000000:address-0x08000000+size],size);return 1
checks=[]
for row in csv.DictReader((p/'hidden-page-3615-image-copies.csv').open()):
 args=[int(row['source'],16),int(row['destination'],16)]+[int(row[k]) for k in ['width','height','source_stride','destination_stride']]
 owned=P();size=Z();assert d.nf_indexed_copy_create(read,None,*args,C.byref(owned),C.byref(size))
 try:
  available=False;page=U();offset=U();indices=P();count=Z()
  assert d.nf_indexed_copy_view(owned,size.value,C.byref(page),C.byref(offset),C.byref(indices),C.byref(count))
  data=C.string_at(indices,count.value)
  blob=C.string_at(owned,size.value)
  assert page.value==0 and offset.value==6720 and count.value==15136
  assert data==rom[args[0]-0x08000000:args[0]-0x08000000+15136]
  assert count.value==reference['checks'][len(checks)]['written_bytes']
  checks.append(dict(refresh=int(row['refresh']),indices_sha256=hashlib.sha256(data).hexdigest(),bytes_exact=15136,tail_bytes_exact=16,source_reader_disabled_lifetime=True))
 finally:d.nf_indexed_copy_free(owned);available=True
bad_cases=[]
for index,value in [(0,0x02000000),(0,0x09fffffe),(1,0x060095fc),(2,239),(3,62),(4,256),(5,256)]:
 bad=args.copy();bad[index]=value;owned=P(123);size=Z(456)
 assert not d.nf_indexed_copy_create(read,None,*bad,C.byref(owned),C.byref(size)) and owned.value==123 and size.value==456
 bad_cases.append([index,value])
available=False;owned=P(123);size=Z(456)
assert not d.nf_indexed_copy_create(read,None,*args,C.byref(owned),C.byref(size)) and owned.value==123 and size.value==456
invalid_views=0
for field,value in [(0,0),(1,2),(2,0x02000000),(3,2),(4,38400),(5,239),(6,62),(7,256),(8,256),(9,15120)]:
 damaged=bytearray(blob);struct.pack_into('<I',damaged,field*4,value);buffer=C.create_string_buffer(bytes(damaged))
 page=U(99);offset=U(98);indices=P(123);count=Z(456)
 assert not d.nf_indexed_copy_view(buffer,len(blob),C.byref(page),C.byref(offset),C.byref(indices),C.byref(count))
 assert (page.value,offset.value,indices.value,count.value)==(99,98,123,456);invalid_views+=1
report=dict(result='PASS',checks=checks,atomic_invalid_abi_cases=len(bad_cases),atomic_reader_failure=True,atomic_corrupt_asset_cases=invalid_views,scope='Owned original indexed image copy asset component, exact validated ABI and16byte tail. Not live scene/GPU integration or playable-port proof.')
(p/'owned-indexed-copy-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
