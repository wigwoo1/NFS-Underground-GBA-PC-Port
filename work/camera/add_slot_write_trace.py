from pathlib import Path
p=Path('work/camera/world_trace.h');s=p.read_text();needle='static FILE*owned_model_builder_file;'
code='''static FILE*owned_slot_file;
API int nf_owned_slot_trace(const char*path){if(owned_slot_file)fclose(owned_slot_file);owned_slot_file=path?fopen(path,"wb"):NULL;return owned_slot_file!=NULL;}
'''
s=s.replace(needle,code+needle);needle='static void world_trace(struct ARMCore*cpu,unsigned pc){'
code='''
 if(owned_slot_file&&(pc==0x08023a16||pc==0x080239ea)){
  unsigned object=cpu->gprs[4],value=(pc==0x08023a16?cpu->gprs[0]:cpu->gprs[1])&255;
  if(validmem(object,164)){uint32_t h[8]={0x31534c4e,c->frameCounter(c),pc,object,c->busRead8(c,object+136),value,rd16(object+54),rd16(object+10)};fwrite(h,32,1,owned_slot_file);}
 }
'''
s=s.replace(needle,needle+code);p.write_text(s)
p=Path('work/camera/run_owned_native_prototype.py');s=p.read_text();needle="d.nf_owned_model_builder_trace.argtypes=[C.c_char_p];assert d.nf_owned_model_builder_trace(str(model_pose_trace.with_suffix('.builders.bin')).encode())"
assert needle in s;s=s.replace(needle,needle+"\n    d.nf_owned_slot_trace.argtypes=[C.c_char_p];assert d.nf_owned_slot_trace(str(model_pose_trace.with_suffix('.slots.bin')).encode())")
s=s.replace('d.nf_owned_model_builder_trace(None);','d.nf_owned_slot_trace.argtypes=[C.c_char_p];d.nf_owned_slot_trace(None);d.nf_owned_model_builder_trace(None);');p.write_text(s)
