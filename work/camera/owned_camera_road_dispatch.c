#include <stdint.h>
#include <stddef.h>
extern void *nf_road_scratch_clone(const void*);
extern void nf_road_scratch_destroy(void*);
extern int nf_road_camera_ring(const double*,unsigned,const void*,const int32_t*,const uint32_t*,double*,unsigned,unsigned*);
extern int nf_road_scratch_ring(void*,uint32_t,const double*,unsigned,unsigned,double*,uint64_t*);
extern int nf_road_clip_continuous(const double*,unsigned,double,double,const uint32_t*,double*,unsigned,unsigned*);
extern int nf_road_scratch_commit(void*,uint32_t,unsigned,const double*,unsigned);
extern int nf_road_scratch_assign(void*,const void*);
__declspec(dllexport) int nf_camera_road_dispatch(void *scratch,const double *camera,unsigned n,const void *attributes,unsigned affine,double left,double right,uint32_t base,unsigned first,const uint32_t *table,int commit,double *out,unsigned *amount,unsigned *projected,uint64_t *missing){
 if(!scratch||!camera||!attributes||!table||!out||!amount||!projected||!missing||n<3||n>32||affine>1||first>64||(commit!=0&&commit!=1))return 0;
 void *temporary=nf_road_scratch_clone(scratch);if(!temporary)return 0;
 double points[320],ring[384];unsigned count=0,result_count=0;uint64_t mask=0;int result=0;const int32_t projection[3]={120,87,128};
 if(!nf_road_camera_ring(camera,n,attributes,projection,table,points,64,&count))goto done;
 if(!nf_road_scratch_ring(temporary,base,points,count,affine,ring,&mask))goto done;
 if(!nf_road_clip_continuous(ring,count,left,right,table,out,128,&result_count))goto done;
 if(!nf_road_scratch_commit(temporary,base,first,out,result_count))goto done;
 if(commit&&!nf_road_scratch_assign(scratch,temporary))goto done;
 *amount=result_count;*projected=count;*missing=mask;result=1;
done:nf_road_scratch_destroy(temporary);return result;
}
