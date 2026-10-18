#include "nfsug_owned_text.h"
JNIEXPORT jboolean JNICALL Java_org_codex_nfsugpreview_NativeMenuCapture_enableNative(JNIEnv*e,jclass c,jlong h,jboolean enabled){(void)e;(void)c;return nfa_core_capture_text_enable(handle(h),enabled)?JNI_TRUE:JNI_FALSE;}
JNIEXPORT jbyteArray JNICALL Java_org_codex_nfsugpreview_NativeMenuCapture_bundleNative(JNIEnv*e,jclass c,jlong h){
 (void)c;uint64_t info[5];if(!nfa_core_capture_layer_info(handle(h),info))return NULL;size_t bytes=nfa_core_capture_menu_text_bundle(handle(h),info[0],(unsigned)info[1],NULL,0);if(!bytes)return NULL;if(bytes!=158904){fail(e,"java/lang/IllegalStateException","Owned menu bundle size");return NULL;}
 void*copy=malloc(bytes);if(!copy){fail(e,"java/lang/OutOfMemoryError","Owned menu bundle");return NULL;}jbyteArray result=NULL;
 if(nfa_core_capture_menu_text_bundle(handle(h),info[0],(unsigned)info[1],copy,bytes)==bytes){result=(*e)->NewByteArray(e,(jsize)bytes);if(result)(*e)->SetByteArrayRegion(e,result,0,(jsize)bytes,(const jbyte*)copy);}free(copy);return result;
}
