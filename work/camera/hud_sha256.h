#ifndef NF_HUD_SHA256_H
#define NF_HUD_SHA256_H
#include <windows.h>
#include <bcrypt.h>
#include <stdint.h>
#include <stdlib.h>
/* Provider/module live for this process; each call owns its hash context. */
static INIT_ONCE nf_sha_once=INIT_ONCE_STATIC_INIT;
static HMODULE nf_sha_module;
static BCRYPT_ALG_HANDLE nf_sha_alg;
static ULONG nf_sha_object_size;
static __typeof__(&BCryptOpenAlgorithmProvider) nf_sha_open;
static __typeof__(&BCryptGetProperty) nf_sha_property;
static __typeof__(&BCryptCreateHash) nf_sha_create;
static __typeof__(&BCryptHashData) nf_sha_update;
static __typeof__(&BCryptFinishHash) nf_sha_finish;
static __typeof__(&BCryptDestroyHash) nf_sha_destroy;
static __typeof__(&BCryptCloseAlgorithmProvider) nf_sha_close;
static BOOL CALLBACK nf_sha_initialize(PINIT_ONCE once,PVOID parameter,PVOID*context){
 (void)once;(void)parameter;(void)context;
 nf_sha_module=LoadLibraryExW(L"bcrypt.dll",NULL,LOAD_LIBRARY_SEARCH_SYSTEM32);if(!nf_sha_module)return FALSE;
#define RESOLVE(field,name) field=(__typeof__(field))GetProcAddress(nf_sha_module,name)
 RESOLVE(nf_sha_open,"BCryptOpenAlgorithmProvider");RESOLVE(nf_sha_property,"BCryptGetProperty");RESOLVE(nf_sha_create,"BCryptCreateHash");RESOLVE(nf_sha_update,"BCryptHashData");RESOLVE(nf_sha_finish,"BCryptFinishHash");RESOLVE(nf_sha_destroy,"BCryptDestroyHash");RESOLVE(nf_sha_close,"BCryptCloseAlgorithmProvider");
#undef RESOLVE
 ULONG got=0;int ok=nf_sha_open&&nf_sha_property&&nf_sha_create&&nf_sha_update&&nf_sha_finish&&nf_sha_destroy&&nf_sha_close;
 if(ok)ok=nf_sha_open(&nf_sha_alg,BCRYPT_SHA256_ALGORITHM,NULL,0)==0;
 if(ok)ok=nf_sha_property(nf_sha_alg,BCRYPT_OBJECT_LENGTH,(PUCHAR)&nf_sha_object_size,sizeof(nf_sha_object_size),&got,0)==0&&got==sizeof(nf_sha_object_size)&&nf_sha_object_size>0&&nf_sha_object_size<=1048576;
 if(!ok){if(nf_sha_alg&&nf_sha_close)nf_sha_close(nf_sha_alg,0);nf_sha_alg=NULL;FreeLibrary(nf_sha_module);nf_sha_module=NULL;return FALSE;}
 return TRUE;
}
static int nf_hud_sha256(uint64_t epoch,const uint8_t*data,size_t bytes,uint8_t output[32]){
 if(!data||!output||bytes>ULONG_MAX||getenv("NF_TEST_HUD_SHA_FAIL")||!InitOnceExecuteOnce(&nf_sha_once,nf_sha_initialize,NULL,NULL))return 0;
 BCRYPT_HASH_HANDLE hash=NULL;PUCHAR object=malloc(nf_sha_object_size);if(!object)return 0;
 int ok=nf_sha_create(nf_sha_alg,&hash,object,nf_sha_object_size,NULL,0,0)==0;
 if(ok)ok=nf_sha_update(hash,(PUCHAR)&epoch,8,0)==0;
 if(ok)ok=nf_sha_update(hash,(PUCHAR)data,(ULONG)bytes,0)==0;
 if(ok)ok=nf_sha_finish(hash,output,32,0)==0;
 if(hash&&nf_sha_destroy(hash)!=0)ok=0;
 free(object);return ok;
}
#endif
