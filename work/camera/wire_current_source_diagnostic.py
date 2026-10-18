from pathlib import Path
p=Path('work/camera/run_owned_native_prototype.py');s=p.read_text();marker='  graph_checks.append(dict(refresh=candidate,'
code='''  current_api=d.nf_owned_current_sources_closed_read;current_api.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
  cn=C.c_size_t();assert current_api(epoch,candidate,None,0,C.byref(cn))
  current_sources=C.create_string_buffer(cn.value);assert current_api(epoch,candidate,current_sources,cn.value,C.byref(cn))
  ch=struct.unpack_from('<6IQ',current_sources.raw)
  assert ch[:3]==(0x31534f4e,1,candidate) and ch[5]==168 and ch[6]==epoch and len(current_sources)==32+ch[4]*168
  assert not current_api(epoch+1,candidate,None,0,C.byref(C.c_size_t()))
'''
assert marker in s;s=s.replace(marker,code+marker)
s=s.replace("('builders',builder_snapshot.raw[:bn.value])):","('builders',builder_snapshot.raw[:bn.value]),('current-sources',current_sources.raw)):")
p.write_text(s)
