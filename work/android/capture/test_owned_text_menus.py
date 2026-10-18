import ctypes as C,os,hashlib,json,struct,sys,subprocess
from pathlib import Path
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port'); out=Path(r'C:\NFSUG-Workspace\NFSUG-android-owned-text-local')
if os.environ.get('NF_TEST_RACING_OWNED_CAPTURE')!='1':
 env=os.environ.copy();env['NF_TEST_RACING_OWNED_CAPTURE']='1'
 raise SystemExit(subprocess.call([sys.executable,__file__],env=env))
with os.add_dll_directory(r'C:\msys64\mingw64\bin'): d=C.CDLL(str(out/'capture-owned-text-host.dll'))
def api(name,args,ret=C.c_int):
 f=getattr(d,'nfa_core_'+name);f.argtypes=args;f.restype=ret;return f
P=C.c_void_p; Q=C.c_uint64; U=C.c_uint; S=C.c_size_t
op=api('open',[C.c_char_p],P); close=api('close',[P],None);load=api('load_state',[P,P,S]);step=api('step',[P,U]);pixels=api('pixels',[P],P)
en=api('capture_enable',[P,C.c_int]);layers=api('capture_layers',[P,C.c_int]);texten=api('capture_text_enable',[P,C.c_int]);infof=api('capture_layer_info',[P,C.POINTER(Q)]);txt=api('capture_text',[P,Q,U,P,S],S);timing=api('timing',[P,C.POINTER(Q)]);audio=api('read_audio',[P,P,S],S)
diag=d.nf_owned_text_diagnostic;diag.argtypes=[Q,U,C.POINTER(Q)];diag.restype=C.c_int
glyphcount=d.nf_owned_text_glyph_count;glyphcount.restype=U
trace=d.nf_owned_text_trace;trace.argtypes=[C.c_char_p];trace.restype=C.c_int

txt=api('capture_menu_text',[P,Q,U,P,S],S)
rowcopy=api('capture_layer_row',[P,Q,U,U,P,S],S)
pair=api('capture_menu_text_bundle',[P,Q,U,P,S],S)
results=[]
for j in range(9):
 state_path=root/f'work/fix-menu/menu-{j}.state';state=state_path.read_bytes();baseline=[]
 for capture in (False,True):
  h=op(os.fsencode(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'));assert h
  frames=coverage=0;contexts=set();last=None
  try:
   assert load(h,state,len(state))
   if capture:assert en(h,1) and layers(h,1) and texten(h,1) and trace(os.fsencode(out/f'menu-{j}-trace'))
   for i in range(90):
    assert step(h,128 if 15<=i<17 else 0)==1
    digest=hashlib.sha256(C.string_at(pixels(h),153600)).hexdigest()
    if not capture:baseline.append(digest);continue
    assert digest==baseline[i]
    info=(Q*5)()
    if not infof(h,info):continue
    contexts.add(tuple(info[2:5]));n=txt(h,info[0],info[1],None,0)
    if n:
     assert n==76880
     sentinel=C.create_string_buffer(bytes([165])*n,n)
     assert not txt(h,info[0],info[1],sentinel,n-1) and sentinel.raw==bytes([165])*n
     assert not txt(h,info[0]+1,info[1],sentinel,n) and sentinel.raw==bytes([165])*n
     buf=C.create_string_buffer(n);assert txt(h,info[0],info[1],buf,n)==n;frames+=1;last=(info[0],info[1])
     assert struct.unpack_from('<10Q',buf.raw)==(0x31544d4e,1,n,info[0],info[1],240,160,info[2],info[3],2)
     assert set(buf.raw[38480:])<={0,1}
     for y in range(160):
      cov=buf.raw[38480+y*240:38480+(y+1)*240]
      if any(cov):
       row=C.create_string_buffer(100480);assert rowcopy(h,info[0],info[1],y,row,100480)==100480
       display=struct.unpack_from('<H',row.raw,8)[0];base=128+((display>>4)&1)*0xa000+y*240
       assert all(not c or buf.raw[80+y*240+x]==row.raw[base+x] for x,c in enumerate(cov))
     pixels_covered=sum(buf.raw[38480:]);coverage+=pixels_covered
     if pixels_covered:
      (out/f'menu-{j}-positive.nft').write_bytes(buf.raw)
      palettes=bytearray()
      for y in range(160):
       row=C.create_string_buffer(100480);assert rowcopy(h,info[0],info[1],y,row,100480)==100480
       palettes+=row.raw[98432:98944]
      (out/f'menu-{j}-positive.nmp').write_bytes(struct.pack('<5Q',0x31504d4e,1,81960,info[0],info[1])+palettes)
      pairbytes=64+76880+81960;joined=C.create_string_buffer(bytes([165])*pairbytes,pairbytes)
      assert pair(h,info[0],info[1],None,0)==pairbytes
      assert not pair(h,info[0],info[1],joined,pairbytes-1) and joined.raw==bytes([165])*pairbytes
      assert not pair(h,info[0]+1,info[1],joined,pairbytes) and joined.raw==bytes([165])*pairbytes
      assert pair(h,info[0],info[1],joined,pairbytes)==pairbytes
      assert struct.unpack_from('<8Q',joined.raw)==(0x31424d4e,1,pairbytes,info[0],info[1],76880,81960,0)
      assert joined.raw[64:76944]==buf.raw
      assert joined.raw[76944:]==struct.pack('<5Q',0x31504d4e,1,81960,info[0],info[1])+palettes
      (out/f'menu-{j}-positive.nmb').write_bytes(joined.raw)

   if capture:
    count=glyphcount();assert trace(None)
    if last:assert load(h,state,len(state)) and not txt(h,*last,None,0) and not pair(h,*last,None,0)
  finally:close(h)
 rows=(out/f'menu-{j}-trace.calls.csv').read_text().splitlines()[1:]
 result=dict(menu=j,state_sha256=hashlib.sha256(state).hexdigest(),frames=90,original_pixels_identical=True,glyph_calls=count,raw_target_hits=sum(r.split(',')[2]=='0806fc60' for r in rows),text_snapshots=frames,covered_pixels=coverage,contexts=sorted(contexts));results.append(result);print(result,flush=True)
assert results[4]['covered_pixels']>0 and results[4]['text_snapshots']>0
(out/'menu-text-sweep-report.json').write_text(json.dumps(results,indent=2))




