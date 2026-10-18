/* Producer-owned original audio; never changes simulation frequency or waits for output. */
#include <mgba/core/blip_buf.h>
static unsigned nf_audio_rate,nf_audio_owner;
static uint64_t nf_audio_samples_read;
API int nf_original_audio_configure(unsigned rate){
 if(!c||(rate!=44100&&rate!=48000))return 0;
 if(nf_audio_owner&&nf_audio_owner!=GetCurrentThreadId())return 0;
 blip_t*l=c->getAudioChannel(c,0),*r=c->getAudioChannel(c,1);if(!l||!r)return 0;
 blip_clear(l);blip_clear(r);blip_set_rates(l,c->frequency(c),rate);blip_set_rates(r,c->frequency(c),rate);
 nf_audio_rate=rate;nf_audio_owner=GetCurrentThreadId();nf_audio_samples_read=0;return 1;
}
API int nf_original_audio_available(unsigned out[2]){
 if(!c||!nf_audio_rate||!out||nf_audio_owner!=GetCurrentThreadId())return 0;
 out[0]=blip_samples_avail(c->getAudioChannel(c,0));out[1]=blip_samples_avail(c->getAudioChannel(c,1));return 1;
}
/* Returns stereo frames, not individual channel samples. Destination is caller-owned. */
API int nf_original_audio_read(int16_t*out,unsigned capacity){
 if(!c||!nf_audio_rate||!out||!capacity||capacity>4096||nf_audio_owner!=GetCurrentThreadId())return -1;
 blip_t*l=c->getAudioChannel(c,0),*r=c->getAudioChannel(c,1);
 unsigned a=blip_samples_avail(l),b=blip_samples_avail(r),n=a<b?a:b;if(n>capacity)n=capacity;
 if(!n)return 0;
 int left=blip_read_samples(l,out,n,1),right=blip_read_samples(r,out+1,n,1);
 if(left!=(int)n||right!=(int)n)return -2;
 nf_audio_samples_read+=n;return n;
}
API int nf_original_audio_clear(void){
 if(!c||!nf_audio_rate||nf_audio_owner!=GetCurrentThreadId())return 0;
 blip_clear(c->getAudioChannel(c,0));blip_clear(c->getAudioChannel(c,1));return 1;
}
API int nf_original_audio_info(uint64_t out[3]){
 if(!c||!out||!nf_audio_rate||nf_audio_owner!=GetCurrentThreadId())return 0;
 out[0]=nf_audio_rate;out[1]=c->frequency(c);out[2]=nf_audio_samples_read;return 1;
}
static void nf_original_audio_retire(void){nf_audio_rate=nf_audio_owner=0;nf_audio_samples_read=0;}
