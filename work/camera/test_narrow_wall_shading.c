#include <assert.h>
#include <stdio.h>
#include "narrow_wall_shading.h"
int main(void){
 double x[2]={119,121},z[2]={100,100},shade[2]={0,15};int a[3240],b[3240];
 assert(nf_narrow_wall_shades(x,z,shade,a,3240));
 for(unsigned i=0;i<3240;i++){
  double p=(i+.5)*240/3240;int expected=p<=119?0:p>=121?15:(int)floor((p-119)*7.5+1e-10);
  assert(a[i]==expected);
 }
 z[1]=200;
 assert(nf_narrow_wall_shades(x,z,shade,a,1)&&a[0]==5);
 assert(nf_narrow_wall_shades(x,z,shade,a,3240));
 double rx[2]={121,119},rz[2]={200,100},rs[2]={15,0};
 assert(nf_narrow_wall_shades(rx,rz,rs,b,3240));
 for(unsigned i=0;i<3240;i++)assert(a[i]==b[i]);
 shade[0]=shade[1]=9;
 assert(nf_narrow_wall_shades(x,z,shade,a,3240));
 for(unsigned i=0;i<3240;i++)assert(a[i]==9);
 z[0]=0;assert(!nf_narrow_wall_shades(x,z,shade,a,3240));
 z[0]=100;x[0]=NAN;assert(!nf_narrow_wall_shades(x,z,shade,a,3240));
 puts("PASS native pixel-center ramp, perspective midpoint, reversed endpoints, constant intensity, invalid input");
 return 0;
}
