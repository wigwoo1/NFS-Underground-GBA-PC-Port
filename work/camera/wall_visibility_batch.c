#include <stdint.h>
#include <stddef.h>
#include <math.h>
typedef struct{double edge[8],bounds[4];uint32_t flags,hidden,active;} In;
typedef struct{uint32_t reason,flags;double x[2],y[4];} Out;
static int64_t sign32(uint32_t v){return v<0x80000000u?v:(int64_t)v-0x100000000ll;}
static int64_t shift(int64_t v,unsigned n){int64_t d=1ll<<n;return v>=0?v/d:-((-v+d-1)/d);}
static double blend(double a,double b,double f){return a==b||f==0?a:f==1?b:a+(b-a)*f;}
static double delta_cell(int64_t t,int64_t s,int64_t d,double fd,const uint32_t*r){uint32_t factor=(uint32_t)t*r[s];double a=(double)shift(d*(int64_t)factor,24);return fd==0?a:blend(a,(double)shift((d+1)*(int64_t)factor,24),fd);}
static double delta_span(int64_t t,int64_t s,int64_t d,double fs,double fd,const uint32_t*r){double a=delta_cell(t,s,d,fd,r);return fs==0?a:blend(a,delta_cell(t,s+1,d,fd,r),fs);}
static double delta(double travel,double span,double difference,const uint32_t*r){int64_t t=(int64_t)floor(travel),s=(int64_t)floor(span),d=(int64_t)floor(difference);double ft=travel-t,fs=span-s,fd=difference-d,a=delta_span(t,s,d,fs,fd,r);return ft==0?a:blend(a,delta_span(t+1,s,d,fs,fd,r),ft);}
static double coord_cell(int64_t x,int64_t a,int64_t b,double f,int center){int64_t half=shift(x,1);return blend(center+shift(sign32((uint32_t)(a*half)),16),center+shift(sign32((uint32_t)(b*half)),16),f);}
static double coord(double x,double z,uint32_t scale,int center,const uint32_t*r){int64_t dz=(int64_t)floor(z),vx=(int64_t)floor(x),a=shift(sign32(r[dz]*scale),7),b=shift(sign32(r[dz+1]*scale),7);double fx=x-vx,fz=z-dz,left=coord_cell(vx,a,b,fz,center);return fx==0||(vx&1)==0?left:blend(left,coord_cell(vx+1,a,b,fz,center),fx);}
__declspec(dllexport) int nf_wall_visibility_batch(const In*in,size_t n,int near,uint32_t scale,int cx,int cy,const uint32_t*r,size_t count,Out*out){
 if(!in||!r||!out||!n||n>4096||count<3)return 0;
 for(size_t i=0;i<n;i++){
 const In*v=in+i;Out*o=out+i;*o=(Out){0};
 for(int j=0;j<8;j++)if(!isfinite(v->edge[j]))return -1;
 for(int j=0;j<4;j++)if(!isfinite(v->bounds[j]))return -1;
 if(v->hidden){o->reason=1;continue;}if(!v->active){o->reason=2;continue;}
 double x=v->edge[0],nx=v->edge[1],z=v->edge[2],nz=v->edge[3],y[4];for(int j=0;j<4;j++)y[j]=v->edge[j+4];uint32_t flags=v->flags;
 if(z<near&&nz<near){o->reason=3;continue;}
 if(z<near||nz<near){int start=z<near;double travel=near-(start?z:nz),span=start?nz-z:z-nz;if(span<1||span>=count-1)return -2;
 double adjust=delta(travel,span,nx-x,r);if(start){x+=adjust;z=near;flags|=8;}else{nx-=adjust;nz=near;flags|=16;}
 for(int j=0;j<4;j+=2){adjust=delta(travel,span,y[j+1]-y[j],r);if(start)y[j]+=adjust;else y[j+1]-=adjust;}
 }
 if(z<1||nz<1||z>=count-1||nz>=count-1)return -3;
 double left=coord(x,z,scale,cx,r),right=coord(nx,nz,scale,cx,r);if((flags&0x2000)&&right<left)flags|=2;if(flags&2){double a=left;left=right;right=a;}
 o->x[0]=left;o->x[1]=right;o->flags=flags;
 if(right<=left||right<v->bounds[0]||left>=v->bounds[1]){o->reason=4;o->flags|=4;continue;}
 for(int j=0;j<4;j++)o->y[j]=coord(y[j],j%2?nz:z,scale,cy,r);
 if(o->y[0]>=v->bounds[3]&&o->y[1]>=v->bounds[3]&&o->y[2]<v->bounds[2]&&o->y[3]<v->bounds[2])o->reason=5;
 }
 return 1;
}
