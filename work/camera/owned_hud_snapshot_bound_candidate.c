#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define HUD_BYTES (160u*34944u)
#define HUD_SLOTS 8
typedef struct {uint64_t token,epoch;unsigned refresh,refs;uint8_t*bytes;uintptr_t source;} HudOwner;
static SRWLOCK lock=SRWLOCK_INIT;static HudOwner owners[HUD_SLOTS];static uint64_t serial,used;
static HudOwner*find(uint64_t token,uint64_t epoch){for(unsigned i=0;i<HUD_SLOTS;i++)if(owners[i].token==token&&owners[i].epoch==epoch&&owners[i].bytes)return owners+i;return NULL;}
__declspec(dllexport) uint64_t nf_hud_owner_create(const void*data,size_t n,uint64_t epoch,unsigned refresh){
 if(!data||n!=HUD_BYTES||!epoch)return 0;const uint8_t*p=data;
 for(unsigned y=0;y<160;y++){uint32_t r,row;memcpy(&r,p+y*34944,4);memcpy(&row,p+y*34944+4,4);if(r!=refresh||row!=y)return 0;}
 AcquireSRWLockExclusive(&lock);unsigned slot=HUD_SLOTS;for(unsigned i=0;i<HUD_SLOTS;i++)if(!owners[i].bytes){slot=i;break;}
 if(slot==HUD_SLOTS||serial==UINT64_MAX){ReleaseSRWLockExclusive(&lock);return 0;}
 uint8_t*copy=malloc(n);if(!copy){ReleaseSRWLockExclusive(&lock);return 0;}memcpy(copy,data,n);uint64_t token=++serial;owners[slot]=(HudOwner){token,epoch,refresh,1,copy,(uintptr_t)data};used+=n;ReleaseSRWLockExclusive(&lock);return token;
}
/* View acquires a lease. Caller must release the token after its last read. */
__declspec(dllexport) int nf_hud_owner_view(uint64_t token,uint64_t epoch,const void**out,unsigned*refresh){
 if(!token||!epoch||!out||!refresh)return 0;AcquireSRWLockExclusive(&lock);HudOwner*o=find(token,epoch);if(!o||o->refs==UINT32_MAX){ReleaseSRWLockExclusive(&lock);return 0;}o->refs++;*out=o->bytes;*refresh=o->refresh;ReleaseSRWLockExclusive(&lock);return 1;
}
__declspec(dllexport) int nf_hud_owner_release(uint64_t token,uint64_t epoch){
 if(!token||!epoch)return 0;AcquireSRWLockExclusive(&lock);HudOwner*o=find(token,epoch);if(!o){ReleaseSRWLockExclusive(&lock);return 0;}if(!--o->refs){free(o->bytes);used-=HUD_BYTES;memset(o,0,sizeof(*o));}ReleaseSRWLockExclusive(&lock);return 1;
}
__declspec(dllexport) int nf_hud_owner_stats(uint64_t*out){if(!out)return 0;AcquireSRWLockShared(&lock);uint64_t active=0,refs=0;for(unsigned i=0;i<HUD_SLOTS;i++){active+=!!owners[i].bytes;refs+=owners[i].refs;}out[0]=active;out[1]=used;out[2]=refs;ReleaseSRWLockShared(&lock);return 1;}

/* Address is an association witness only; never dereferenced after creation.
Private caller retains the original immutable source through every lease. */
__declspec(dllexport) int nf_hud_owner_source_matches(uint64_t token,uint64_t epoch,const void*source,unsigned refresh){AcquireSRWLockShared(&lock);HudOwner*o=find(token,epoch);int ok=o&&o->source==(uintptr_t)source&&o->refresh==refresh;ReleaseSRWLockShared(&lock);return ok;}
