#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "audio_queue_duration.h"
int main(void){
 NFAudioQueueClock c={0};uint64_t remaining=777;
 assert(nf_audio_clock_remaining(&c,0,&remaining)&&remaining==0);
 nf_audio_clock_submit(&c,4096);assert(nf_audio_clock_remaining(&c,441,&remaining)&&remaining==3655);
 nf_audio_clock_submit(&c,1770);assert(nf_audio_clock_remaining(&c,441,&remaining)&&remaining==5425);
 remaining=777;assert(!nf_audio_clock_remaining(&c,440,&remaining)&&remaining==777&&c.last==441);
 assert(!nf_audio_clock_remaining(&c,6000,&remaining)&&remaining==777&&c.last==441);
 assert(nf_audio_clock_remaining(&c,442,&remaining)&&remaining==5424);
 nf_audio_clock_reset(&c);assert(!c.submitted&&!c.high&&!c.last&&!c.valid);
 remaining=777;assert(!nf_audio_clock_remaining(&c,1,&remaining)&&remaining==777&&!c.valid);
 c.submitted=(1ull<<32)+8192;assert(nf_audio_clock_remaining(&c,0xfffffff0u,&remaining)&&remaining==8208);
 assert(nf_audio_clock_remaining(&c,32,&remaining)&&remaining==8160&&c.high==(1ull<<32));
 remaining=777;assert(!nf_audio_clock_remaining(&c,31,&remaining)&&remaining==777&&c.last==32);
 nf_audio_clock_reset(&c);nf_audio_clock_submit(&c,17);assert(nf_audio_clock_remaining(&c,17,&remaining)&&remaining==0&&!c.high);
 puts("PASS_AUDIO_CLOCK_DURATION_RESET_INVALID_NONMONOTONIC_WRAP");return 0;
}
