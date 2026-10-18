from pathlib import Path
p=Path('work/probe.c');s=p.read_text().replace('static unsigned dt_percent=100;','static unsigned dt_percent=100;\nstatic int normalize_steering;\nstatic uint64_t steering_previous;\nstatic unsigned steering_cycles=280896;')
s=s.replace('unsigned pc=cpu->gprs[15]-2,op=cpu->prefetch[0];','''unsigned pc=cpu->gprs[15]-2,op=cpu->prefetch[0];
 if(normalize_steering&&pc==0x080095e8){uint64_t t=mTimingGlobalTime(c->timing);steering_cycles=steering_previous?(unsigned)(t-steering_previous):280896;steering_previous=t;}
 if(normalize_steering&&pc==0x080097ee){
  /* Research hypothesis: preserve the observed four-refresh reference ramp.
     This does not normalize the rest of the physics or the clamp timing. */
  cpu->gprs[7]=(int32_t)((int64_t)(int32_t)cpu->gprs[7]*steering_cycles/(4*280896));
 }
''')
s=s.replace('calls_file||timing_file||dt_percent!=100','calls_file||timing_file||dt_percent!=100||normalize_steering')
s=s.replace('API void nf_debug(unsigned pc)', 'API void nf_normalize_steering(int enabled){normalize_steering=enabled;steering_previous=0;nfsThumbTrace=(calls_file||timing_file||dt_percent!=100||normalize_steering)?thumbTrace:NULL;}\nAPI void nf_debug(unsigned pc)')
p.write_text(s)
