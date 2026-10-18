from pathlib import Path
p=Path('work/v2/gpu.c');s=p.read_text();pos=s.index('void nf_gpu_draw(')
code=r'''
/* Presentation interpolation only: it never changes emulated memory or clocks. */
static NFPoly motion_previous[NF_MAX_POLYS],motion_current[NF_MAX_POLYS];
static int motion_matches[NF_MAX_POLYS],motion_count,motion_enabled=1;
static unsigned motion_version;
static double motion_start,motion_interval=1.0/15.0;
unsigned nf_scene_version(void);
static double motion_now(void){LARGE_INTEGER q,f;QueryPerformanceCounter(&q);QueryPerformanceFrequency(&f);return (double)q.QuadPart/f.QuadPart;}
void nf_gpu_motion(int enabled){motion_enabled=enabled;motion_count=0;motion_start=0;}
static float match_cost(const NFPoly*a,const NFPoly*b){
 if(a->kind!=b->kind||a->address!=b->address||a->shade!=b->shade||a->count!=b->count||a->width!=b->width||a->height!=b->height||a->stride!=b->stride)return 1e20f;
 float cost=0;
 for(unsigned j=0;j<a->count;j++){
  const NFVertex*x=&a->v[j],*y=&b->v[j];if(x->q<=0||y->q<=0)return 1e20f;
  float dx=x->x-y->x,dy=x->y-y->y,du=x->s/x->q-y->s/y->q,dv=x->t/x->q-y->t/y->q;
  if(fabsf(dx)>45||fabsf(dy)>45)return 1e20f;
  if(a->kind==2&&(fabsf(du)>.001f||fabsf(dv)>.001f))return 1e20f;
  if(a->kind==3&&fabsf(dx)>0.01f)return 1e20f;
  cost+=dx*dx+dy*dy+400*(du*du+dv*dv);
 }
 return cost/a->count;
}
static void motion_prepare(const NFPoly* polys,int n,double now){
 unsigned version=nf_scene_version();if(version==motion_version&&motion_count)return;
 int previous_count=motion_count;memcpy(motion_previous,motion_current,previous_count*sizeof(NFPoly));
 memcpy(motion_current,polys,n*sizeof(NFPoly));motion_count=n;
 unsigned char used[NF_MAX_POLYS]={0};
 for(int i=0;i<n;i++){
  int best=-1;float cost=1600;
  for(int j=0;j<previous_count;j++)if(!used[j]){float candidate=match_cost(&polys[i],&motion_previous[j]);if(candidate<cost){best=j;cost=candidate;}}
  motion_matches[i]=best;if(best>=0)used[best]=1;
 }
 if(motion_start){double interval=now-motion_start;if(interval>=.025&&interval<=.2)motion_interval=interval;}
 motion_start=now;motion_version=version;
}
'''
s=s[:pos]+code+s[pos:]
s=s.replace('for(int i=0;i<poly_count;i++)polygon(&polys[i]);',r'''int interpolate=motion_enabled&&nf_read(0x03005f14,4)==5;
  double clock=motion_now();if(interpolate)motion_prepare(polys,poly_count,clock);else motion_count=0;
  float alpha=motion_interval>0?(float)((clock-motion_start)/motion_interval):1;if(alpha<0)alpha=0;if(alpha>1)alpha=1;
  for(int i=0;i<poly_count;i++){
   if(interpolate&&motion_matches[i]>=0){
    NFPoly blended=motion_current[i];const NFPoly* old=&motion_previous[motion_matches[i]];
    for(unsigned j=0;j<blended.count;j++){
     NFVertex* v=&blended.v[j];const NFVertex* a=&old->v[j];
     v->x=a->x+(v->x-a->x)*alpha;v->y=a->y+(v->y-a->y)*alpha;
     v->s=a->s+(v->s-a->s)*alpha;v->t=a->t+(v->t-a->t)*alpha;v->q=a->q+(v->q-a->q)*alpha;
    }
    polygon(&blended);
   }else polygon(&polys[i]);
  }''')
s=s.replace('const NFPoly* polys=nf_scene(&poly_count);','const NFPoly* polys=nf_scene(&poly_count);\n if(!poly_count)motion_count=0;')
p.write_text(s)
p=Path('work/v2/gpu.h');s=p.read_text().replace('unsigned nf_gpu_frame_hash(void);','unsigned nf_gpu_frame_hash(void);\nvoid nf_gpu_motion(int);');p.write_text(s)
p=Path('work/host.c');s=p.read_text().replace('gpu_ready,mode60=1','gpu_ready,mode60=0');s=s.replace('static int focus_paused;','static int focus_paused;\nstatic int smooth_motion=1;')
start=s.index('  if(w==VK_F4 && ready)');end=s.index('\n',start)
s=s[:start]+'  if(w==VK_F4 && ready){smooth_motion=!smooth_motion;nf_gpu_motion(smooth_motion);status(smooth_motion?"Geometry interpolation ON; original simulation timing":"Geometry interpolation OFF; original simulation timing");}'+s[end:]
s=s.replace('F4: experimental 60 Hz game updates (physics differs)','F4: geometry interpolation (simulation stays original)')
s=s.replace('else if(!strcmp(argv[i],"--experimental-60"))mode60=1;','else if(!strcmp(argv[i],"--no-smoothing"))smooth_motion=0;')
s=s.replace('nf_60(mode60);','nf_60(0);')
s=s.replace('gpu_ready=nf_gpu_init();','gpu_ready=nf_gpu_init();nf_gpu_motion(smooth_motion);')
s=s.replace('NFSUG 60 Hz Active','NFSUG Motion Interpolation')
s=s.replace('mode60?"4K / EXPERIMENTAL 60 Hz":"4K / original timing"','smooth_motion?"4K interpolation / original logic":"4K / original timing"')
s=s.replace('motion %.1f fps','source %.1f fps')
p.write_text(s)
