#include <stdint.h>
#include <string.h>
#include "road_source_attributes.h"
typedef void *(*Clone)(const void*);
typedef void (*Destroy)(void*);
typedef int (*Camera)(const double*,unsigned,const NFRoadSourceAttributes*,const int32_t*,const uint32_t*,double*,unsigned,unsigned*);
typedef int (*Ring)(void*,uint32_t,const double*,unsigned,unsigned,double*,uint64_t*);
typedef int (*Clip)(const double*,unsigned,double,double,const uint32_t*,double*,unsigned,unsigned*);
typedef int (*Commit)(void*,uint32_t,unsigned,const double*,unsigned);
typedef int (*Assign)(void*,const void*);
/* Same ordered operations and isolated scratch as the Python reference.
   Nothing publishes until every operation succeeds. Function pointers belong
   to the retained probe DLL; this helper owns no global game state. */
__declspec(dllexport) int nf_camera_clip_transaction(void *const *fn,void *scratch,const double *camera,unsigned n,const NFRoadSourceAttributes *attrs,const double *bounds,uint32_t base,unsigned first,const uint32_t *table,int assign,double *out,unsigned capacity,unsigned *projected,unsigned *amount,uint64_t *missing){
 if(!fn||!scratch||!camera||!attrs||!bounds||!table||!out||!projected||!amount||!missing||n!=attrs->count||n>32||first>64||capacity<128||assign<0||assign>1)return 0;
 for(unsigned i=0;i<7;i++)if(!fn[i])return 0;
 void *temporary=((Clone)fn[0])(scratch);if(!temporary)return 0;
 double points[320],ring[384],clipped[768];int32_t projection[3]={120,87,128};unsigned count=0,size=0;uint64_t mask=0;int ok=0;
 if(!((Camera)fn[2])(camera,n,attrs,projection,table,points,64,&count))goto done;
 if(!((Ring)fn[3])(temporary,base,points,count,attrs->affine,ring,&mask))goto done;
 if(!((Clip)fn[4])(ring,count,bounds[0],bounds[1],table,clipped,128,&size))goto done;
 if(!((Commit)fn[5])(temporary,base,first,clipped,size))goto done;
 if(assign&&!((Assign)fn[6])(scratch,temporary))goto done;
 memcpy(out,clipped,size*6*sizeof(double));*projected=count;*amount=size;*missing=mask;ok=1;
 done:((Destroy)fn[1])(temporary);return ok;
}
