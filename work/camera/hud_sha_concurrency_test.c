#include <stdio.h>
#include <string.h>
#include "hud_sha256.h"
static HANDLE start;
static int expect_failure;
static const uint8_t expected[32]={0x91,0xb9,0x62,0x9e,0x85,0xe3,0xe3,0x0e,0xe5,0x37,0x7f,0xac,0x0e,0x93,0x78,0xbe,0x74,0xb0,0x71,0x9a,0xf3,0x6d,0x0c,0x88,0x03,0x74,0xdf,0x20,0x52,0x8b,0x70,0x41};
static DWORD WINAPI worker(void*unused){(void)unused;if(WaitForSingleObject(start,10000)!=WAIT_OBJECT_0)return 1;for(unsigned i=0;i<128;i++){uint8_t out[32];memset(out,0xa5,32);int ok=nf_hud_sha256(123,(const uint8_t*)"abc",3,out);if(expect_failure){if(ok||out[0]!=0xa5)return 2;}else if(!ok||memcmp(out,expected,32))return 3;}return 0;}
static int round_run(int failure){expect_failure=failure;start=CreateEvent(NULL,TRUE,FALSE,NULL);if(!start)return 0;HANDLE threads[8];for(unsigned i=0;i<8;i++){threads[i]=CreateThread(NULL,0,worker,NULL,0,NULL);if(!threads[i])return 0;}if(!SetEvent(start)||WaitForMultipleObjects(8,threads,TRUE,20000)!=WAIT_OBJECT_0)return 0;for(unsigned i=0;i<8;i++){DWORD result;if(!GetExitCodeThread(threads[i],&result)||result||!CloseHandle(threads[i]))return 0;}return CloseHandle(start);}
int main(void){if(!round_run(0))return 1;DWORD before,after;if(!GetProcessHandleCount(GetCurrentProcess(),&before))return 2;for(unsigned i=0;i<8;i++)if(!round_run(0))return 3;_putenv("NF_TEST_HUD_SHA_FAIL=1");if(!round_run(1))return 4;_putenv("NF_TEST_HUD_SHA_FAIL=");if(!round_run(0)||!GetProcessHandleCount(GetCurrentProcess(),&after)||before!=after)return 5;printf("SHA_CONCURRENT_FIRST_INIT_THREADS8_SUCCESS_DIGESTS10240_FAILCLOSED1024_RECOVERY_HANDLE_COUNT_STABLE=PASS handles=%lu\n",(unsigned long)after);return 0;}
