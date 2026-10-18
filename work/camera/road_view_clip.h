/* Continuous projected geometry; independent of original raster padding. */
static unsigned road_view_clip_mode(const RoadVertex *in,unsigned count,RoadVertex *out,double left,double right,double top,double bottom,unsigned affine){
 RoadVertex buffers[2][8];unsigned n=count;
 if(count>3||left>right||top>bottom)return 0;
 for(unsigned i=0;i<n;i++)buffers[0][i]=in[i];
 for(unsigned side=0;side<4;side++){
  RoadVertex *src=buffers[side%2],*dst=buffers[1-side%2];unsigned m=0;double bound=side==0?left:side==1?right:side==2?top:bottom;
  for(unsigned i=0;i<n;i++){
   RoadVertex a=src[(i+n-1)%n],b=src[i];double av=side<2?a.p.x:a.p.y,bv=side<2?b.p.x:b.p.y;
   int ai=side%2?av<=bound:av>=bound,bi=side%2?bv<=bound:bv>=bound;
   if(ai!=bi){double t=(bound-av)/(bv-av),qa=1/a.p.z,qb=1/b.p.z,q=qa+(qb-qa)*t;
    if(m>=8||q<=0)return 0;
    dst[m++]=(RoadVertex){{a.p.x+(b.p.x-a.p.x)*t,a.p.y+(b.p.y-a.p.y)*t,1/q},(a.u*qa+(b.u*qb-a.u*qa)*t)/q,(a.v*qa+(b.v*qb-a.v*qa)*t)/q};
    if(affine){dst[m-1].u=a.u+(b.u-a.u)*t;dst[m-1].v=a.v+(b.v-a.v)*t;}
   }
   if(ai!=bi){if(side<2)dst[m-1].p.x=bound;else dst[m-1].p.y=bound;}
   if(bi){if(m>=8)return 0;dst[m++]=b;}
  }n=m;
 }
 for(unsigned i=0;i<n;i++){out[i]=buffers[0][i];}
 return n;
}
static unsigned road_view_clip(const RoadVertex *in,unsigned count,RoadVertex *out,double left,double right,double top,double bottom){return road_view_clip_mode(in,count,out,left,right,top,bottom,0);}

