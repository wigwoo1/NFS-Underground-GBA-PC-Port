#ifndef NF_PC_AUDIO_POSITION_PROBE_H
#define NF_PC_AUDIO_POSITION_PROBE_H
/* Optional, owner-thread, read-only driver probe. Never used for scheduling.
   TIME_SAMPLES is per-channel frames; reject alternate units. A reset begins
   a fresh position/submission epoch. Not an end-to-end audible latency meter. */
typedef struct {unsigned frame,stage,epoch,queued,ring,type,error,valid,comparable;uint64_t produced,submitted,played,remaining;double time,lag,query_ms,core,capture,publish,lock,audio,logic;} NFAPRow;
static NFAPRow nf_ap_rows[16384];static unsigned nf_ap_count,nf_ap_overflow,nf_ap_epoch,nf_ap_last_valid,nf_ap_last,nf_ap_frame;static uint64_t nf_ap_submitted,nf_ap_high,nf_ap_base;static double nf_ap_deadline;static int nf_ap_initialized;static const char*nf_ap_path;
static int nf_ap_enabled(void){if(!nf_ap_initialized){nf_ap_path=getenv("NF_AUDIO_POSITION_CSV");nf_ap_initialized=1;}return nf_ap_path&&nf_ap_path[0];}
static void nf_ap_reset(void){if(!nf_ap_enabled())return;nf_ap_epoch++;nf_ap_submitted=nf_ap_high=0;nf_ap_last_valid=nf_ap_last=0;nf_ap_base=audio_frames;}
static void nf_ap_context(uint64_t frame,double deadline){if(!nf_ap_enabled())return;nf_ap_frame=(unsigned)frame;nf_ap_deadline=deadline;}
static void nf_ap_submit(unsigned frames){if(nf_ap_enabled())nf_ap_submitted+=frames;}
static void nf_ap_sample(unsigned stage){
 if(!nf_ap_enabled()||!audio_device)return;
 if(nf_ap_count==16384){nf_ap_overflow++;return;}
 NFAPRow*r=nf_ap_rows+nf_ap_count++;memset(r,0,sizeof(*r));r->frame=nf_ap_frame;r->stage=stage;r->epoch=nf_ap_epoch;r->ring=audio_count;r->produced=audio_frames-nf_ap_base;r->submitted=nf_ap_submitted;r->time=now();r->lag=(r->time-nf_ap_deadline)*1000;
 for(unsigned i=0;i<8;i++)r->queued+=(wave[i].dwFlags&WHDR_INQUEUE)!=0;
 MMTIME position;memset(&position,0,sizeof(position));position.wType=TIME_SAMPLES;double start=now();r->error=waveOutGetPosition(audio_device,&position,sizeof(position));r->query_ms=(now()-start)*1000;r->type=position.wType;
 if(!r->error&&position.wType==TIME_SAMPLES){
  unsigned value=position.u.sample;int monotonic=1;
  if(nf_ap_last_valid&&value<nf_ap_last){if(nf_ap_last>0xf0000000u&&value<0x10000000u)nf_ap_high+=1ull<<32;else monotonic=0;}
  r->played=nf_ap_high+value;r->valid=(unsigned)monotonic;
  if(monotonic){nf_ap_last=value;nf_ap_last_valid=1;if(r->played<=r->submitted){r->comparable=1;r->remaining=r->submitted-r->played;}}
 }
 r->core=metrics[M_CORE].total;r->capture=metrics[M_CAPTURE].total;r->publish=metrics[M_PUBLISH].total;r->lock=metrics[M_LOCK].total;r->audio=metrics[M_AUDIO].total;r->logic=metrics[M_LOGIC].total;
}
static void nf_ap_finish(void){
 if(!nf_ap_enabled())return;
 FILE*f=fopen(nf_ap_path,"w");if(!f)return;
 fputs("frame,stage,epoch,time,deadline_lag_ms,queued_buffers,ring_frames,produced_frames,submitted_frames,played_frames,remaining_frames,position_type,position_error,position_valid,remaining_comparable,query_ms,core_total_ms,capture_total_ms,publish_total_ms,lock_total_ms,audio_total_ms,logic_total_ms,overflow_rows\n",f);
 for(unsigned i=0;i<nf_ap_count;i++){const NFAPRow*r=nf_ap_rows+i;fprintf(f,"%u,%u,%u,%.9f,%.6f,%u,%u,%llu,%llu,%llu,%llu,%u,%u,%u,%u,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%u\n",r->frame,r->stage,r->epoch,r->time,r->lag,r->queued,r->ring,(unsigned long long)r->produced,(unsigned long long)r->submitted,(unsigned long long)r->played,(unsigned long long)r->remaining,r->type,r->error,r->valid,r->comparable,r->query_ms,r->core,r->capture,r->publish,r->lock,r->audio,r->logic,nf_ap_overflow);}
 fclose(f);
}
#endif
