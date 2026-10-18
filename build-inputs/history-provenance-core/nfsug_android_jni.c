#include "nfsug_android_core.h"
#include <jni.h>
#include <stdint.h>
#include <stdlib.h>
#define JNI_NAME(n) Java_org_codex_nfsugpreview_NativeCore_##n
static NFAAndroidCore* handle(jlong h){return (NFAAndroidCore*)(uintptr_t)h;}
static void fail(JNIEnv*e,const char*type,const char*message){
 jclass c=(*e)->FindClass(e,type);if(c)(*e)->ThrowNew(e,c,message);
}
JNIEXPORT jlong JNICALL JNI_NAME(openNative)(JNIEnv*e,jclass c,jstring path){
 (void)c;if(!path)return 0;
 const char*s=(*e)->GetStringUTFChars(e,path,NULL);if(!s)return 0;
 NFAAndroidCore*h=nfa_core_open(s);(*e)->ReleaseStringUTFChars(e,path,s);
 return (jlong)(uintptr_t)h;
}
JNIEXPORT void JNICALL JNI_NAME(closeNative)(JNIEnv*e,jclass c,jlong h){(void)e;(void)c;nfa_core_close(handle(h));}
JNIEXPORT jint JNICALL JNI_NAME(stepNative)(JNIEnv*e,jclass c,jlong h,jint keys){(void)e;(void)c;return nfa_core_step(handle(h),(uint32_t)keys);}
JNIEXPORT jboolean JNICALL JNI_NAME(pauseNative)(JNIEnv*e,jclass c,jlong h,jboolean pause){(void)e;(void)c;return nfa_core_pause(handle(h),pause)?JNI_TRUE:JNI_FALSE;}
JNIEXPORT jlongArray JNICALL JNI_NAME(timingNative)(JNIEnv*e,jclass c,jlong h){
 (void)c;uint64_t t[4];if(!nfa_core_timing(handle(h),t))return NULL;
 jlong values[4];for(int i=0;i<4;i++)values[i]=(jlong)t[i];
 jlongArray a=(*e)->NewLongArray(e,4);if(a)(*e)->SetLongArrayRegion(e,a,0,4,values);return a;
}
JNIEXPORT jboolean JNICALL JNI_NAME(frameNative)(JNIEnv*e,jclass c,jlong h,jobject buffer){
 (void)c;
 const uint32_t*p=nfa_core_pixels(handle(h));
 if(!p||!buffer)return JNI_FALSE;
 unsigned char*out=(*e)->GetDirectBufferAddress(e,buffer);
 jlong capacity=(*e)->GetDirectBufferCapacity(e,buffer);
 if(!out||capacity<240*160*4)return JNI_FALSE;
 for(size_t i=0;i<240*160;i++){
  uint32_t v=p[i];out[i*4]=(unsigned char)v;out[i*4+1]=(unsigned char)(v>>8);
  out[i*4+2]=(unsigned char)(v>>16);out[i*4+3]=255;
 }
 return JNI_TRUE;
}
JNIEXPORT jint JNICALL JNI_NAME(audioNative)(JNIEnv*e,jclass c,jlong h,jshortArray output){
 (void)c;if(!output)return 0;
 jsize count=(*e)->GetArrayLength(e,output);
 if(count<2||count>8192||(count&1))return 0;
 int16_t samples[8192];
 size_t frames=nfa_core_read_audio(handle(h),samples,(size_t)count/2);
 if(frames)(*e)->SetShortArrayRegion(e,output,0,(jsize)(frames*2),(const jshort*)samples);
 return (jint)frames;
}
JNIEXPORT jbyteArray JNICALL JNI_NAME(snapshotNative)(JNIEnv*e,jclass c,jlong h,jboolean battery){
 (void)c;size_t bytes=battery?nfa_core_battery_size(handle(h)):nfa_core_state_size(handle(h));
 if(!bytes)return NULL;
 if(bytes>1024*1024){fail(e,"java/lang/IllegalStateException","Core snapshot exceeds limit");return NULL;}
 unsigned char*copy=malloc(bytes);if(!copy){fail(e,"java/lang/OutOfMemoryError","Core snapshot allocation");return NULL;}
 int ok=battery?nfa_core_copy_battery(handle(h),copy,bytes)==bytes:nfa_core_save_state(handle(h),copy,bytes);
 jbyteArray a=NULL;
 if(ok){a=(*e)->NewByteArray(e,(jsize)bytes);if(a)(*e)->SetByteArrayRegion(e,a,0,(jsize)bytes,(const jbyte*)copy);}
 free(copy);return a;
}
JNIEXPORT jboolean JNICALL JNI_NAME(restoreNative)(JNIEnv*e,jclass c,jlong h,jbyteArray input,jboolean battery){
 (void)c;if(!input)return JNI_FALSE;
 jsize bytes=(*e)->GetArrayLength(e,input);
 if(bytes<=0||bytes>1024*1024)return JNI_FALSE;
 if(battery){if(bytes!=512&&bytes!=8192&&bytes!=32768&&bytes!=65536&&bytes!=131072)return JNI_FALSE;}
 else if((size_t)bytes!=nfa_core_state_size(handle(h)))return JNI_FALSE;
 jbyte*data=(*e)->GetByteArrayElements(e,input,NULL);if(!data)return JNI_FALSE;
 int ok=battery?nfa_core_load_battery(handle(h),data,(size_t)bytes):nfa_core_load_state(handle(h),data,(size_t)bytes);
 (*e)->ReleaseByteArrayElements(e,input,data,JNI_ABORT);
 return ok?JNI_TRUE:JNI_FALSE;
}


#ifdef NFA_WITH_NATIVE_CAPTURE
#include "nfsug_capture.h"
#endif
JNIEXPORT jboolean JNICALL JNI_NAME(captureSupportedNative)(JNIEnv*e,jclass c){
 (void)e;(void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 return JNI_TRUE;
#else
 return JNI_FALSE;
#endif
}
JNIEXPORT jboolean JNICALL JNI_NAME(captureEnableNative)(JNIEnv*e,jclass c,jlong h,jboolean enabled){
 (void)e;(void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 return nfa_core_capture_enable(handle(h),enabled)?JNI_TRUE:JNI_FALSE;
#else
 (void)h;(void)enabled;return JNI_FALSE;
#endif
}
JNIEXPORT jlongArray JNICALL JNI_NAME(captureStatsNative)(JNIEnv*e,jclass c,jlong h){
 (void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 uint64_t values[8];if(!nfa_core_capture_stats(handle(h),values))return NULL;
 jlong out[8];for(int i=0;i<8;i++)out[i]=(jlong)values[i];
 jlongArray a=(*e)->NewLongArray(e,8);if(a)(*e)->SetLongArrayRegion(e,a,0,8,out);return a;
#else
 (void)e;(void)h;return NULL;
#endif
}
JNIEXPORT jbyteArray JNICALL JNI_NAME(capturePacketNative)(JNIEnv*e,jclass c,jlong h){
 (void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 size_t bytes=nfa_core_capture_copy(handle(h),NULL,0);if(!bytes)return NULL;
 if(bytes>256u*1024u*1024u){fail(e,"java/lang/IllegalStateException","Native scene exceeds packet limit");return NULL;}
 void*copy=malloc(bytes);if(!copy){fail(e,"java/lang/OutOfMemoryError","Native scene copy");return NULL;}
 if(nfa_core_capture_copy(handle(h),copy,bytes)!=bytes){free(copy);return NULL;}
 jbyteArray a=(*e)->NewByteArray(e,(jsize)bytes);
 if(a)(*e)->SetByteArrayRegion(e,a,0,(jsize)bytes,(const jbyte*)copy);
 free(copy);return a;
#else
 (void)e;(void)h;return NULL;
#endif
}

JNIEXPORT jboolean JNICALL JNI_NAME(captureLayersNative)(JNIEnv*e,jclass c,jlong h,jboolean enabled){
 (void)e;(void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 return nfa_core_capture_layers(handle(h),enabled)?JNI_TRUE:JNI_FALSE;
#else
 (void)h;(void)enabled;return JNI_FALSE;
#endif
}
JNIEXPORT jbyteArray JNICALL JNI_NAME(captureSceneNative)(JNIEnv*e,jclass c,jlong h){
 (void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 uint64_t info[5];if(!nfa_core_capture_layer_info(handle(h),info))return NULL;
 size_t bytes=nfa_core_capture_bundle(handle(h),info[0],(unsigned)info[1],NULL,0);if(!bytes)return NULL;
 if(bytes>64u*1024u*1024u){fail(e,"java/lang/IllegalStateException","Combined scene exceeds limit");return NULL;}
 void*copy=malloc(bytes);if(!copy){fail(e,"java/lang/OutOfMemoryError","Combined scene allocation");return NULL;}
 if(nfa_core_capture_bundle(handle(h),info[0],(unsigned)info[1],copy,bytes)!=bytes){free(copy);return NULL;}
 jbyteArray a=(*e)->NewByteArray(e,(jsize)bytes);if(a)(*e)->SetByteArrayRegion(e,a,0,(jsize)bytes,(const jbyte*)copy);free(copy);return a;
#else
 (void)e;(void)h;return NULL;
#endif
}

JNIEXPORT jboolean JNICALL JNI_NAME(captureSourceWorldEnableNative)(JNIEnv*e,jclass c,jlong h,jboolean enabled){
 (void)e;(void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 return nfa_core_capture_source_world_enable(handle(h),enabled)?JNI_TRUE:JNI_FALSE;
#else
 (void)h;(void)enabled;return JNI_FALSE;
#endif
}
JNIEXPORT jbyteArray JNICALL JNI_NAME(captureSourceWorldNative)(JNIEnv*e,jclass c,jlong h,jlong epoch,jlong serial,jlong begin,jlong end){
 (void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 if(epoch<=0||serial<0||serial>UINT32_MAX||begin<0||begin>UINT32_MAX||end<begin||end>UINT32_MAX)return NULL;
 size_t bytes=nfa_core_capture_source_world(handle(h),(uint64_t)epoch,(unsigned)serial,(unsigned)begin,(unsigned)end,NULL,0);if(!bytes)return NULL;
 if(bytes>64u*1024u*1024u){fail(e,"java/lang/IllegalStateException","Source scene exceeds limit");return NULL;}
 void*copy=malloc(bytes);if(!copy){fail(e,"java/lang/OutOfMemoryError","Source scene allocation");return NULL;}
 if(nfa_core_capture_source_world(handle(h),(uint64_t)epoch,(unsigned)serial,(unsigned)begin,(unsigned)end,copy,bytes)!=bytes){free(copy);return NULL;}
 jbyteArray a=(*e)->NewByteArray(e,(jsize)bytes);if(a)(*e)->SetByteArrayRegion(e,a,0,(jsize)bytes,(const jbyte*)copy);free(copy);return a;
#else
 (void)e;(void)h;(void)epoch;(void)serial;(void)begin;(void)end;return NULL;
#endif
}

JNIEXPORT jboolean JNICALL JNI_NAME(captureWallHistoryEnableNative)(JNIEnv*e,jclass c,jlong h,jboolean enabled){
 (void)e;(void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 return nfa_core_capture_wall_history_enable(handle(h),enabled)?JNI_TRUE:JNI_FALSE;
#else
 (void)h;(void)enabled;return JNI_FALSE;
#endif
}
JNIEXPORT jbyteArray JNICALL JNI_NAME(captureWallHistoryNative)(JNIEnv*e,jclass c,jlong h,jlong epoch,jlong serial,jlong begin,jlong end){
 (void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 if(epoch<=0||serial<0||serial>UINT32_MAX||begin<0||begin>UINT32_MAX||end<begin||end>UINT32_MAX)return NULL;
 size_t bytes=nfa_core_capture_wall_history(handle(h),(uint64_t)epoch,(unsigned)serial,(unsigned)begin,(unsigned)end,NULL,0);if(!bytes)return NULL;
 if(bytes>64u*1024u*1024u){fail(e,"java/lang/IllegalStateException","Wall history exceeds limit");return NULL;}
 void*copy=malloc(bytes);if(!copy){fail(e,"java/lang/OutOfMemoryError","Wall history allocation");return NULL;}
 if(nfa_core_capture_wall_history(handle(h),(uint64_t)epoch,(unsigned)serial,(unsigned)begin,(unsigned)end,copy,bytes)!=bytes){free(copy);return NULL;}
 jbyteArray a=(*e)->NewByteArray(e,(jsize)bytes);if(a)(*e)->SetByteArrayRegion(e,a,0,(jsize)bytes,(const jbyte*)copy);free(copy);return a;
#else
 (void)e;(void)h;(void)epoch;(void)serial;(void)begin;(void)end;return NULL;
#endif
}

JNIEXPORT jlongArray JNICALL JNI_NAME(captureWallHistoryStatsNative)(JNIEnv*e,jclass c,jlong h){
 (void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 uint64_t values[8];if(!nfa_core_capture_wall_history_stats(handle(h),values))return NULL;
 jlong out[8];for(int i=0;i<8;i++)out[i]=(jlong)values[i];
 jlongArray a=(*e)->NewLongArray(e,8);if(a)(*e)->SetLongArrayRegion(e,a,0,8,out);return a;
#else
 (void)e;(void)h;return NULL;
#endif
}
JNIEXPORT jbyteArray JNICALL JNI_NAME(captureRoadHistoryNative)(JNIEnv*e,jclass c,jlong h,jlong epoch,jlong serial,jlong begin,jlong end){
 (void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 if(epoch<=0||serial<0||serial>UINT32_MAX||begin<0||begin>UINT32_MAX||end<begin||end>UINT32_MAX)return NULL;
 size_t bytes=nfa_core_capture_road_history(handle(h),(uint64_t)epoch,(unsigned)serial,(unsigned)begin,(unsigned)end,NULL,0);if(!bytes)return NULL;
 if(bytes>64u*1024u*1024u){fail(e,"java/lang/IllegalStateException","Road history exceeds limit");return NULL;}
 void*copy=malloc(bytes);if(!copy){fail(e,"java/lang/OutOfMemoryError","Road history allocation");return NULL;}
 if(nfa_core_capture_road_history(handle(h),(uint64_t)epoch,(unsigned)serial,(unsigned)begin,(unsigned)end,copy,bytes)!=bytes){free(copy);return NULL;}
 jbyteArray a=(*e)->NewByteArray(e,(jsize)bytes);if(a)(*e)->SetByteArrayRegion(e,a,0,(jsize)bytes,(const jbyte*)copy);free(copy);return a;
#else
 (void)e;(void)h;(void)epoch;(void)serial;(void)begin;(void)end;return NULL;
#endif
}

JNIEXPORT jbyteArray JNICALL JNI_NAME(captureWriteOwnershipNative)(JNIEnv*e,jclass c,jlong h,jlong epoch,jlong serial,jlong begin,jlong end){
 (void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 if(epoch<=0||serial<0||serial>UINT32_MAX||begin<0||begin>UINT32_MAX||end<begin||end>UINT32_MAX)return NULL;
 size_t bytes=nfa_core_capture_write_ownership(handle(h),(uint64_t)epoch,(unsigned)serial,(unsigned)begin,(unsigned)end,NULL,0);if(!bytes)return NULL;
 if(bytes>64u*1024u*1024u){fail(e,"java/lang/IllegalStateException","Write ownership exceeds limit");return NULL;}
 void*copy=malloc(bytes);if(!copy){fail(e,"java/lang/OutOfMemoryError","Write ownership allocation");return NULL;}
 if(nfa_core_capture_write_ownership(handle(h),(uint64_t)epoch,(unsigned)serial,(unsigned)begin,(unsigned)end,copy,bytes)!=bytes){free(copy);return NULL;}
 jbyteArray a=(*e)->NewByteArray(e,(jsize)bytes);if(a)(*e)->SetByteArrayRegion(e,a,0,(jsize)bytes,(const jbyte*)copy);free(copy);return a;
#else
 (void)e;(void)h;(void)epoch;(void)serial;(void)begin;(void)end;return NULL;
#endif
}

JNIEXPORT jbyteArray JNICALL JNI_NAME(captureBackgroundSceneNative)(JNIEnv*e,jclass c,jlong h){
 (void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 uint64_t info[5];if(!nfa_core_capture_layer_info(handle(h),info))return NULL;
 size_t bytes=nfa_core_capture_background_scene(handle(h),info[0],(unsigned)info[1],NULL,0);if(!bytes)return NULL;
 if(bytes>64u*1024u*1024u){fail(e,"java/lang/IllegalStateException","Source background exceeds limit");return NULL;}
 void*copy=malloc(bytes);if(!copy){fail(e,"java/lang/OutOfMemoryError","Source background allocation");return NULL;}
 if(nfa_core_capture_background_scene(handle(h),info[0],(unsigned)info[1],copy,bytes)!=bytes){free(copy);return NULL;}
 jbyteArray a=(*e)->NewByteArray(e,(jsize)bytes);if(a)(*e)->SetByteArrayRegion(e,a,0,(jsize)bytes,(const jbyte*)copy);free(copy);return a;
#else
 (void)e;(void)h;return NULL;
#endif
}

JNIEXPORT jboolean JNICALL JNI_NAME(captureSkyEnableNative)(JNIEnv*e,jclass c,jlong h,jboolean enabled){
 (void)e;(void)c;
#ifdef NFA_WITH_NATIVE_CAPTURE
 return nfa_core_capture_sky_enable(handle(h),enabled)?JNI_TRUE:JNI_FALSE;
#else
 (void)h;(void)enabled;return JNI_FALSE;
#endif
}