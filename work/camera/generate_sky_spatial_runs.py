from pathlib import Path
p=Path('work/camera');s=(p/'owned_gpu_sky_spatial_batch.c').read_text()
s=s.replace('static const uint8_t*sky_lower,*sky_upper;static double sky_weight;','static const uint8_t*sky_lower,*sky_upper;static double sky_weight;\nstatic unsigned sky_spatial_vertex_count;')
s=s.replace('   double positions[4][2]', '''   unsigned char rgba[4]={(r<<3)|(r>>2),(g<<3)|(g>>2),(b<<3)|(b>>2),255};
   if(at>=4){
    SkySpatialVertex*previous=vertices+at-4;
    if(previous[0].y==y&&previous[1].x==left&&!memcmp(previous[0].rgba,rgba,4)){
     previous[1].x=right;previous[2].x=right;continue;
    }
   }
   double positions[4][2]''')
s=s.replace('glDrawArrays(GL_QUADS,0,vertex_count);','sky_spatial_vertex_count=at;glDrawArrays(GL_QUADS,0,at);')
s+='\n__declspec(dllexport) unsigned nf_sky_spatial_vertex_count(void){return sky_spatial_vertex_count;}\n'
(p/'owned_gpu_sky_spatial_runs.c').write_text(s)
