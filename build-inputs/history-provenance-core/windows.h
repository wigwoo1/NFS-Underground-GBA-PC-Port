#ifndef NF_ANDROID_CAPTURE_WINDOWS_SHIM
#define NF_ANDROID_CAPTURE_WINDOWS_SHIM
#ifdef _WIN32
#include_next <windows.h>
#else
#include <stdint.h>
#include <time.h>
#define __declspec(x)
typedef struct {int64_t QuadPart;} LARGE_INTEGER;
static inline int QueryPerformanceFrequency(LARGE_INTEGER*t){t->QuadPart=1000000000;return 1;}
static inline int QueryPerformanceCounter(LARGE_INTEGER*t){struct timespec now;if(clock_gettime(CLOCK_MONOTONIC,&now))return 0;t->QuadPart=(int64_t)now.tv_sec*1000000000+now.tv_nsec;return 1;}
#endif
#endif
