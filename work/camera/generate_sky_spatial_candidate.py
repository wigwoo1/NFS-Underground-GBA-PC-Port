from pathlib import Path
p=Path('work/camera');s=(p/'owned_gpu_source_context_candidate.c').read_text()
begin=s.index(' if(sky_upper&&sky_weight>0){');end=s.index(' if(sky_stage_profile)sky_stage_ticks[1]',begin)
replacement=''' if(sky_upper&&sky_weight>0){
 /* Isolated diagnostic: move each nearest-source boundary left by phase.
    Upper supplies the next owned texel, including source wrap/partial tail.
    Preserve destination scanline palettes and never filter HUD or geometry. */
 glDisable(GL_TEXTURE_2D);glDisable(GL_ALPHA_TEST);glDisable(GL_BLEND);
 glBegin(GL_QUADS);
 for(unsigned i=10560;i<25696;i++){
  unsigned y=i/240,x=i%240;double split=x+1-sky_weight;
  for(unsigned part=0;part<2;part++){
   uint16_t c;const uint8_t*indices=part?sky_upper:sky_lower;
   memcpy(&c,owned_hud[y].palette+indices[i-10560]*2,2);
   unsigned r=c&31,g=(c>>5)&31,b=(c>>10)&31;
   glColor3ub((r<<3)|(r>>2),(g<<3)|(g>>2),(b<<3)|(b>>2));
   double left=part?split:x,right=part?x+1:split;
   glVertex2d(left,y);glVertex2d(right,y);glVertex2d(right,y+1);glVertex2d(left,y+1);
  }
 }
 glEnd();glEnable(GL_TEXTURE_2D);glEnable(GL_ALPHA_TEST);glColor4f(1,1,1,1);
 }
'''
(p/'owned_gpu_sky_spatial_diagnostic.c').write_text(s[:begin]+replacement+s[end:])
