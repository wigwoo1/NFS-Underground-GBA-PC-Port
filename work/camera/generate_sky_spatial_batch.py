from pathlib import Path
p=Path('work/camera');s=(p/'owned_gpu_sky_spatial_diagnostic.c').read_text()
begin=s.index(' glBegin(GL_QUADS);',s.index(' /* Isolated diagnostic:'));end=s.index('glEnable(GL_TEXTURE_2D);glEnable(GL_ALPHA_TEST);glColor4f',begin)
replacement=''' typedef struct {double x,y;unsigned char rgba[4];} SkySpatialVertex;
 const unsigned vertex_count=15136*8;
 SkySpatialVertex*vertices=malloc(sizeof(*vertices)*vertex_count);if(!vertices)return 26;
 unsigned at=0;
 for(unsigned i=10560;i<25696;i++){
  unsigned y=i/240,x=i%240;double split=x+1-sky_weight;
  for(unsigned part=0;part<2;part++){
   uint16_t c;const uint8_t*indices=part?sky_upper:sky_lower;
   memcpy(&c,owned_hud[y].palette+indices[i-10560]*2,2);
   unsigned r=c&31,g=(c>>5)&31,b=(c>>10)&31;
   double left=part?split:x,right=part?x+1:split;
   double positions[4][2]={{left,y},{right,y},{right,y+1},{left,y+1}};
   for(unsigned j=0;j<4;j++){
    SkySpatialVertex*v=vertices+at++;v->x=positions[j][0];v->y=positions[j][1];
    v->rgba[0]=(r<<3)|(r>>2);v->rgba[1]=(g<<3)|(g>>2);v->rgba[2]=(b<<3)|(b>>2);v->rgba[3]=255;
   }
  }
 }
 glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT);
 glEnableClientState(GL_VERTEX_ARRAY);glEnableClientState(GL_COLOR_ARRAY);glDisableClientState(GL_TEXTURE_COORD_ARRAY);
 glVertexPointer(2,GL_DOUBLE,sizeof(*vertices),&vertices[0].x);
 glColorPointer(4,GL_UNSIGNED_BYTE,sizeof(*vertices),vertices[0].rgba);
 glDrawArrays(GL_QUADS,0,vertex_count);
 glPopClientAttrib();free(vertices);
 '''
(p/'owned_gpu_sky_spatial_batch.c').write_text(s[:begin]+replacement+s[end:])
