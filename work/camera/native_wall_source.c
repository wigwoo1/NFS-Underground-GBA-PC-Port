#include <stdint.h>
#include <string.h>
#include <limits.h>
extern int nf_road_camera_continuous(const double*,const int32_t*,double*);
extern int nf_road_point_project_continuous(const double*,const int32_t*,unsigned,unsigned,const int32_t*,const uint32_t*,double*);
extern int nf_wall_edge_order(int,int,unsigned,int*);
extern int nf_wall_source_uv(const uint8_t*,const uint8_t*,unsigned,unsigned,uint32_t*);
static int16_t wh(const uint8_t*p){int16_t v;memcpy(&v,p,2);return v;}
static int32_t wi(const uint8_t*p){int32_t v;memcpy(&v,p,4);return v;}
/* Continuous camera-space quad for native GPU projection; raw source only. */
__declspec(dllexport) int nf_wall_owned_quad(const uint8_t*source,const uint8_t*offset,const int32_t*matrix,double*out){
 if(!source||!offset||!matrix||!out)return 0;
 double x=(double)wi(source)+wh(offset),z=(double)wi(source+4)+wh(offset+2);
 double nx=(double)wi(source+68)+wh(offset+32),nz=(double)wi(source+72)+wh(offset+34);
 double world[4][3]={{x,wh(source+8)+wh(offset+8),z},{nx,wh(source+12)+wh(offset+8),nz},{nx,wh(source+14)+wh(offset+10),nz},{x,wh(source+10)+wh(offset+10),z}},camera[4][3];
 for(unsigned j=0;j<4;j++)if(!nf_road_camera_continuous(world[j],matrix,camera[j]))return 0;
 memcpy(out,camera,sizeof(camera));return 1;
}
/* Atomic uncut default wall geometry from owned adjacent world endpoints. */
__declspec(dllexport) int nf_wall_owned_prepared(const uint8_t*source,const uint8_t*offset,const uint8_t*animation,const int32_t*matrix,const uint8_t*material,unsigned flags,const uint32_t*table,uint8_t*out){
 if(!source||!offset||!animation||!matrix||!material||!table||!out||flags>65535||(flags&128))return 0;
 double camera[4][3];if(!nf_wall_owned_quad(source,offset,matrix,(double*)camera))return 0;
 int projected[4][3];const int32_t attrs[2]={0,0},projection[3]={120,87,128};
 for(unsigned j=0;j<4;j++){double *point=camera[j],p[5];if(point[2]<64||!nf_road_point_project_continuous(point,attrs,8,128,projection,table,p))return 0;
  projected[j][0]=(int)p[0];projected[j][1]=(int)p[1];projected[j][2]=(int)point[2];
  for(unsigned k=0;k<3;k++)if(projected[j][k]<INT16_MIN||projected[j][k]>INT16_MAX)return 0;
 }
 int ordered[3];uint32_t uv[6];if(!nf_wall_edge_order(projected[0][0],projected[1][0],flags,ordered)||!nf_wall_source_uv(source,animation,(uint16_t)wh(material+36),flags,uv))return 0;
 uint8_t edge[52]={0};int16_t coords[8]={(int16_t)ordered[0],(int16_t)ordered[1],(int16_t)projected[0][2],(int16_t)projected[1][2],(int16_t)projected[0][1],(int16_t)projected[1][1],(int16_t)projected[3][1],(int16_t)projected[2][1]};
 memcpy(edge,coords,16);memcpy(edge+16,uv,24);uint16_t light[2]={(uint16_t)(source[60]<<8),(uint16_t)(source[61]<<8)},f=(uint16_t)ordered[2];memcpy(edge+40,light,4);memcpy(edge+48,&f,2);memcpy(out,edge,52);return 1;
}
