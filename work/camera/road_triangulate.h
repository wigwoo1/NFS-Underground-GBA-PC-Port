#ifndef NF_ROAD_TRIANGULATE_H
#define NF_ROAD_TRIANGULATE_H
static double road_cross(const RoadVertex*a,const RoadVertex*b,const RoadVertex*c){return (b->p.x-a->p.x)*(c->p.y-a->p.y)-(b->p.y-a->p.y)*(c->p.x-a->p.x);}
/* Existing renderer ear clipping, shared with diagnostic GPU probes. */
static unsigned road_triangulate(const RoadVertex*out,unsigned n,RoadVertex*triangles){
 double area=0;int ids[64];for(unsigned i=0;i<n;i++){ids[i]=i;area+=out[i].p.x*out[(i+1)%n].p.y-out[(i+1)%n].p.x*out[i].p.y;}
 double sign=area>=0?1:-1;unsigned triangle_count=0;
 while(n>=3){int found=0;for(unsigned j=0;j<n;j++){
  unsigned prev=(j+n-1)%n,next=(j+1)%n;const RoadVertex*a=out+ids[prev],*b=out+ids[j],*c=out+ids[next];if(road_cross(a,b,c)*sign<1e-8)continue;
  int inside=0;for(unsigned k=0;k<n;k++){if(k==prev||k==j||k==next)continue;const RoadVertex*v=out+ids[k];if(road_cross(a,b,v)*sign>1e-8&&road_cross(b,c,v)*sign>1e-8&&road_cross(c,a,v)*sign>1e-8){inside=1;break;}}
  if(inside)continue;
  triangles[triangle_count++]=*a;triangles[triangle_count++]=*b;triangles[triangle_count++]=*c;for(unsigned k=j;k+1<n;k++)ids[k]=ids[k+1];n--;found=1;break;
 }if(!found)break;}return triangle_count;
}
#endif
