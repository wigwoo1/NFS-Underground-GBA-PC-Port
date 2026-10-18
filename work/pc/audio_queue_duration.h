#ifndef NF_PC_AUDIO_QUEUE_DURATION_H
#define NF_PC_AUDIO_QUEUE_DURATION_H
#include <stdint.h>
/* Device position and successful submissions share a reset epoch. Unknown
 * positions must never justify retaining ready PCM in the producer ring. */
typedef struct {uint64_t submitted,high;uint32_t last;unsigned valid;} NFAudioQueueClock;
static inline void nf_audio_clock_reset(NFAudioQueueClock*c){c->submitted=0;c->high=0;c->last=0;c->valid=0;}
static inline void nf_audio_clock_submit(NFAudioQueueClock*c,unsigned frames){c->submitted+=frames;}
static inline int nf_audio_clock_remaining(NFAudioQueueClock*c,uint32_t raw,uint64_t*remaining){
 uint64_t high=c->high;
 if(c->valid&&raw<c->last){if(c->last>0xf0000000u&&raw<0x10000000u)high+=1ull<<32;else return 0;}
 uint64_t played=high+raw;if(played>c->submitted)return 0;
 c->high=high;c->last=raw;c->valid=1;*remaining=c->submitted-played;return 1;
}
#endif
