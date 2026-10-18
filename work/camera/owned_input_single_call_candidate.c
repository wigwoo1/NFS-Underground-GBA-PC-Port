#include <stdint.h>
#include <stddef.h>
#include <string.h>
#define EXPORT __declspec(dllexport)
typedef int (*Poll)(void);
typedef int (*Snapshot)(uint32_t*);
typedef int (*TimedPoll)(uint64_t*);
typedef int (*Stages)(uint64_t*);
EXPORT int nf_input_poll_snapshot(void *poll,void *snapshot,uint32_t *out,size_t bytes){
 if(!poll||!snapshot||!out||bytes!=4*sizeof(uint32_t))return 37;
 if(((Poll)poll)()!=1)return 38;
 if(((Snapshot)snapshot)(out)!=1)return 39;
 return 1;
}
EXPORT int nf_input_poll_snapshot_timed(void *poll,void *stages,void *snapshot,uint64_t *timing,size_t timing_bytes,uint32_t *out,size_t bytes){
 if(!poll||!stages||!snapshot||!timing||timing_bytes!=5*sizeof(uint64_t)||!out||bytes!=4*sizeof(uint32_t))return 37;
 if(((TimedPoll)poll)(timing)!=1)return 38;
 if(((Stages)stages)(timing+1)!=1)return 40;
 if(((Snapshot)snapshot)(out)!=1)return 39;
 return 1;
}
