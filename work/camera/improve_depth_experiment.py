from pathlib import Path
p=Path('work/camera/preview_resources.h');s=p.read_text().replace('glTexImage2D(GL_TEXTURE_2D,0,0x81a6,3840,2160,0,GL_DEPTH_COMPONENT,GL_UNSIGNED_INT,NULL);','''/* Zero-to-one clipping avoids cancellation of small reciprocal depths. */
 void(APIENTRY*clip_control)(GLenum,GLenum)=(void*)wglGetProcAddress("glClipControl");if(!clip_control)return 29;
 clip_control(0x8ca1,0x935f);
 glTexImage2D(GL_TEXTURE_2D,0,0x8cac,3840,2160,0,GL_DEPTH_COMPONENT,GL_FLOAT,NULL);''');p.write_text(s)
p=Path('work/camera/model_preview.c');s=p.read_text().replace('glDepthFunc(GL_LEQUAL)','glDepthFunc(GL_GEQUAL)').replace('glClearDepth(1)','glClearDepth(0)').replace('glVertex3d(x[i],y[i],2*q[i]-1)','glVertex3d(x[i],y[i],-q[i])');p.write_text(s)
p=Path('work/camera/road_preview.h');s=p.read_text().replace('glVertex3d(v->p.x,v->p.y,2*q-1)','glVertex3d(v->p.x,v->p.y,-q)');p.write_text(s)
p=Path('work/camera/test_preview_depth.c');s=p.read_text().replace('2/z-1','-1/z').replace('(1-1/z)','(1/z)').replace('GL_LEQUAL','GL_GEQUAL').replace('glClearDepth(1)','glClearDepth(0)').replace('32767};','32767,65536,1000000};').replace('nearer drawn first; far color indicates quantized tie or error','nearer drawn first; reversed float depth; far color indicates quantized tie or error');s=s.replace('fclose(precision);','fclose(precision);if(collisions)return 7;');p.write_text(s)
