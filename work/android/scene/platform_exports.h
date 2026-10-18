#ifndef NF_ANDROID_EXPORT_COMPAT
#define NF_ANDROID_EXPORT_COMPAT
#ifndef _WIN32
#define __declspec(attribute) __attribute__((visibility("default")))
#endif
#endif
