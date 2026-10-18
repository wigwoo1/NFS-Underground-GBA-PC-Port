#ifndef NF_ROAD_SPLIT_GPU_H
#define NF_ROAD_SPLIT_GPU_H
static double nf_split_profile_mark(int enabled){if(!enabled)return 0;if(getenv("NF_TEST_SPLIT_PROFILE_SYNC"))glFinish();LARGE_INTEGER now,freq;QueryPerformanceCounter(&now);QueryPerformanceFrequency(&freq);return (double)now.QuadPart*1000/freq.QuadPart;}
/* Native GPU page renders only; no emulatedBGimage or CPU RGB transport. */
static int render_road_split(const void*old,size_t old_size,const void*newer,size_t new_size,unsigned cut,char**argv){
 NFRoadBundle a,b;if(!cut||cut>=160||!preview_keep_context||!nf_road_bundle_view(old,old_size,&a)||!nf_road_bundle_view(newer,new_size,&b)||a.ordered.epoch!=b.ordered.epoch||a.ordered.packet.serial>=b.ordered.packet.serial||a.ordered.packet.page==b.ordered.packet.page)return 44;
 int profile=getenv("NF_TEST_SPLIT_STAGE_PROFILE")!=NULL;double t0=nf_split_profile_mark(profile);
 int result=render_road_bundle(old,old_size,argv);if(result)return result;double t1=nf_split_profile_mark(profile);
 int reuse=getenv("NF_TEST_SPLIT_SCRATCH_REUSE")!=NULL;GLuint saved;
 if(reuse&&preview_split_scratch){saved=preview_split_scratch;glBindTexture(GL_TEXTURE_2D,saved);glCopyTexSubImage2D(GL_TEXTURE_2D,0,0,0,0,0,3840,2160);}
 else{glGenTextures(1,&saved);glBindTexture(GL_TEXTURE_2D,saved);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glCopyTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,0,0,3840,2160,0);if(reuse)preview_split_scratch=saved;}
 double t2=nf_split_profile_mark(profile);
 result=render_road_bundle(newer,new_size,argv);if(result){if(!reuse)glDeleteTextures(1,&saved);return result;}
 double t3=nf_split_profile_mark(profile);
 glPushAttrib(GL_ALL_ATTRIB_BITS);glViewport(0,0,3840,2160);glDisable(GL_SCISSOR_TEST);glDisable(GL_DEPTH_TEST);glDisable(GL_BLEND);glDisable(GL_ALPHA_TEST);glEnable(GL_TEXTURE_2D);glBindTexture(GL_TEXTURE_2D,saved);glColor4f(1,1,1,1);
 glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity();glOrtho(0,3840,2160,0,-1,1);glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity();
 double bottom=ceil(cut*13.5-.5),v=1-bottom/2160.;glBegin(GL_QUADS);glTexCoord2d(0,1);glVertex2d(0,0);glTexCoord2d(1,1);glVertex2d(3840,0);glTexCoord2d(1,v);glVertex2d(3840,bottom);glTexCoord2d(0,v);glVertex2d(0,bottom);glEnd();
 glPopMatrix();glMatrixMode(GL_PROJECTION);glPopMatrix();glMatrixMode(GL_MODELVIEW);glPopAttrib();if(!reuse)glDeleteTextures(1,&saved);double t4=nf_split_profile_mark(profile);if(profile)printf("split_stage_ms serial=%u cut=%u old=%.6f copy=%.6f newer=%.6f compose=%.6f sync=%u\n",b.ordered.packet.serial,cut,t1-t0,t2-t1,t3-t2,t4-t3,getenv("NF_TEST_SPLIT_PROFILE_SYNC")!=NULL);return glGetError()==GL_NO_ERROR?0:45;
}
#endif
