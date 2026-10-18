from pathlib import Path
p=Path('work/camera/preview_resources.h');s=p.read_text();s=s.replace('static GLuint preview_target,preview_fbo;','static GLuint preview_target,preview_fbo;\n#ifdef NF_DIAGNOSTIC_DEPTH\nstatic GLuint preview_depth;\n#endif');s=s.replace('return check(0x8d40)==0x8cd5?0:11;','''
#ifdef NF_DIAGNOSTIC_DEPTH
 glGenTextures(1,&preview_depth);glBindTexture(GL_TEXTURE_2D,preview_depth);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
 glTexImage2D(GL_TEXTURE_2D,0,0x81a6,3840,2160,0,GL_DEPTH_COMPONENT,GL_UNSIGNED_INT,NULL);attach(0x8d40,0x8d00,GL_TEXTURE_2D,preview_depth,0);
#endif
 return check(0x8d40)==0x8cd5?0:11;''');s=s.replace('glDeleteTextures(1,&preview_target);','''#ifdef NF_DIAGNOSTIC_DEPTH
  glDeleteTextures(1,&preview_depth);preview_depth=0;
#endif
  glDeleteTextures(1,&preview_target);''');p.write_text(s)
p=Path('work/camera/model_preview.c');s=p.read_text().replace('glClear(GL_COLOR_BUFFER_BIT);unsigned offset=0,drawn=0;','''#ifdef NF_DIAGNOSTIC_DEPTH
  glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);glDepthMask(GL_TRUE);glClearDepth(1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
#else
  glClear(GL_COLOR_BUFFER_BIT);
#endif
  unsigned offset=0,drawn=0;''').replace('glVertex2d(x[i],y[i]);','''
#ifdef NF_DIAGNOSTIC_DEPTH
    glVertex3d(x[i],y[i],2*q[i]-1);
#else
    glVertex2d(x[i],y[i]);
#endif
''');p.write_text(s)
p=Path('work/camera/road_preview.h');s=p.read_text().replace('glVertex2d(v->p.x,v->p.y);','''
#ifdef NF_DIAGNOSTIC_DEPTH
 glVertex3d(v->p.x,v->p.y,2*q-1);
#else
 glVertex2d(v->p.x,v->p.y);
#endif
''');p.write_text(s)
