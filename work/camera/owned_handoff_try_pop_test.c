#include "owned_frame_handoff.c"
__declspec(dllexport) void nf_test_hold_queue(NFOwnedFrameHandoff*q,HANDLE ready,HANDLE release){EnterCriticalSection(&q->lock);SetEvent(ready);WaitForSingleObject(release,5000);LeaveCriticalSection(&q->lock);}
