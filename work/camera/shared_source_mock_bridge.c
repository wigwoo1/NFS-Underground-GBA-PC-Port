#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
static uint64_t version=1;static unsigned bump_during_build;
__declspec(dllexport) uint64_t nf_page_write_audit_version(void){return version;}
__declspec(dllexport) void nf_mock_observer_reset(void){version++;}
__declspec(dllexport) void nf_mock_reset_during_build(void){bump_during_build=1;}
__declspec(dllexport) void nf_live_ordered_bundle_free(void*p){free(p);}
__declspec(dllexport) int nf_live_completed_road_bundle(uint64_t epoch,unsigned serial,void**out,size_t*size){
 if(epoch!=2||serial!=18||!out||!size)return 0;FILE*f=fopen("work/camera/motion-prepared-original-18.nfrb","rb");if(!f)return 0;fseek(f,0,SEEK_END);size_t n=ftell(f);rewind(f);void*p=malloc(n);if(!p||fread(p,1,n,f)!=n){free(p);fclose(f);return 0;}fclose(f);if(bump_during_build){version++;bump_during_build=0;}*out=p;*size=n;return 1;
}
