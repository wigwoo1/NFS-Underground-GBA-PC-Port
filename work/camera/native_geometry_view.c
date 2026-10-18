#include <stdint.h>
#include <stddef.h>
#include <string.h>
typedef struct {unsigned kind,context;const uint8_t*blocks[12];uint32_t sizes[12];} NFGeometryView;
static uint32_t gvword(const uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static int gvrecord(const uint8_t*p,size_t n,size_t*used,NFGeometryView*v){
 if(n<16||gvword(p)!=0x3147534e||gvword(p+12)!=12)return 0;
 NFGeometryView q={0};q.kind=gvword(p+4);q.context=gvword(p+8);if(q.kind<1||q.kind>3)return 0;
 size_t offset=16;for(unsigned i=0;i<12;i++){if(n-offset<4)return 0;unsigned size=gvword(p+offset);offset+=4;if(size>0x100000||size>n-offset)return 0;q.blocks[i]=p+offset;q.sizes[i]=size;offset+=size;}
 if(q.kind==1){if(q.sizes[6]!=32)return 0;unsigned count=gvword(q.blocks[6]);if(count<3||count>32||q.sizes[0]!=count*68||q.sizes[1]!=count*32||q.sizes[2]!=20||q.sizes[3]!=48||q.sizes[4]!=48||q.sizes[5]!=8||!q.sizes[7]||q.sizes[8]!=512||q.sizes[9]!=48||q.sizes[10]!=64||q.sizes[11]!=64)return 0;}
 if(q.kind==2){const unsigned sizes[12]={136,64,8,48,48,8,64,32,65536,512,52,260};for(unsigned i=0;i<12;i++)if(i!=8&&q.sizes[i]!=sizes[i])return 0;
 if(q.sizes[8]!=65536){uint16_t shift,height;memcpy(&shift,q.blocks[4]+36,2);memcpy(&height,q.blocks[4]+38,2);if(shift>10||!height||height>1024||!q.sizes[8]||q.sizes[8]>65536||(size_t)(1u<<shift)*height>q.sizes[8])return 0;}}
 if(q.kind==3){if(q.sizes[0]!=68||q.sizes[1]!=40||q.sizes[2]!=48||q.sizes[3]!=64||q.sizes[4]%6||!q.sizes[5]||q.sizes[6]%2||q.sizes[7]!=q.sizes[6]||q.sizes[8]%4||q.sizes[9]!=16||!q.sizes[10]||q.sizes[11]!=512)return 0;}
 *v=q;*used=offset;return 1;
}
/* Immutable views borrow the caller-owned packet. Validate the entire packet
   before publishing any views, so a truncated late draw cannot leak a partial scene. */
__declspec(dllexport) int nf_geometry_packet_views(const uint8_t*p,size_t n,NFGeometryView*out,unsigned capacity,unsigned*count){
 if(!p||!n||n>0x800000||!out||!count)return 0;
 size_t offset=0;unsigned total=0;NFGeometryView view;while(offset<n){size_t used;if(!gvrecord(p+offset,n-offset,&used,&view)||total==capacity)return 0;offset+=used;total++;}
 offset=0;for(unsigned i=0;i<total;i++){size_t used;if(!gvrecord(p+offset,n-offset,&used,&view))return 0;out[i]=view;offset+=used;}*count=total;return 1;
}
