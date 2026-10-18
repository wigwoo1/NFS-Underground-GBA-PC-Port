from pathlib import Path
p=Path('work/camera/world_trace.h');s=p.read_text()
s=s.replace('static unsigned owned_builder_count,owned_builder_failed;','static unsigned owned_builder_count,owned_builder_failed;\nstatic unsigned owned_removals[1024][3],owned_removal_count;static uint64_t owned_removal_epoch;')
s=s.replace('static void owned_builder_reset(void){','static void owned_builder_reset(void){owned_removal_count=0;owned_removal_epoch=0;')
s=s.replace('size_t n=32+count*168;uint8_t*data=malloc(n);','size_t n=32+count*176;uint8_t*data=calloc(1,n);')
s=s.replace('0x31534f4e,2,refresh,c->frameCounter(c),count,168','0x31534f4e,3,refresh,c->frameCounter(c),count,176')
s=s.replace('data+32+i*168','data+32+i*176').replace('data+36+i*168','data+36+i*176')
needle='native_read_owned(addresses[i],data+36+i*176,164)){free(data);return 0;}}'
assert needle in s;s=s.replace(needle,'native_read_owned(addresses[i],data+36+i*176,164)){free(data);return 0;}if(owned_removal_epoch==epoch)for(unsigned j=0;j<owned_removal_count;j++)if(owned_removals[j][0]==addresses[i])memcpy(data+200+i*176,owned_removals[j]+1,8);}')
needle='static void world_trace(struct ARMCore*cpu,unsigned pc){'
code='''
 if(owned_graph_live_enabled&&pc==0x0801e4c2){
  uint64_t epoch=nf_native_scene_epoch();if(owned_removal_epoch!=epoch){owned_removal_count=0;owned_removal_epoch=epoch;}
  unsigned address=cpu->gprs[6],at=0;for(;at<owned_removal_count;at++)if(owned_removals[at][0]==address)break;
  if(at==1024)owned_builder_failed=1;else{if(at==owned_removal_count)owned_removal_count++;owned_removals[at][0]=address;owned_removals[at][1]=c->frameCounter(c);owned_removals[at][2]=pc;}
 }
'''
s=s.replace(needle,needle+code);p.write_text(s)
p=Path('work/camera/owned_model_sources.py');s=p.read_text().replace(' sources:object',' sources:object\n removals:object');s=s.replace('version!=2 or stride!=168','(version,stride) not in ((2,168),(3,176))').replace('  sources={}','  sources={};removals={}')
s=s.replace('  return cls(epoch,refresh,source,MappingProxyType(sources))',"   if version==3:\n    time,pc=struct.unpack_from('<2I',raw,200+i*stride)\n    if (time==0)!=(pc==0) or time>source or pc not in (0,0x0801e4c2):raise ValueError('Invalid source removal event')\n    if time:removals[address]=(time,pc)\n  return cls(epoch,refresh,source,MappingProxyType(sources),MappingProxyType(removals))")
p.write_text(s)
p=Path('work/camera/run_owned_native_prototype.py');s=p.read_text().replace('ch[:3]==(0x31534f4e,2,candidate)','ch[:3]==(0x31534f4e,3,candidate)').replace('ch[5]==168','ch[5]==176').replace('32+ch[4]*168','32+ch[4]*176');p.write_text(s)
