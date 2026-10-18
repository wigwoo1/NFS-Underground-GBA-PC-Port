/* Exercise fixed-function draw states before starting the game clock. This
   uses a disposable synthetic texture, never future game frames or assets. */
static int preview_draw_warmup(void){
 GLuint texture;const uint8_t pixels[16]={255,255,255,255,255,255,255,0,255,255,255,255,255,255,255,255};
 glPushAttrib(GL_ALL_ATTRIB_BITS);
 glMatrixMode(GL_PROJECTION);glPushMatrix();glLoadIdentity();glOrtho(0,240,160,0,-1,1);
 glMatrixMode(GL_MODELVIEW);glPushMatrix();glLoadIdentity();glViewport(300,0,3240,2160);
 glGenTextures(1,&texture);glBindTexture(GL_TEXTURE_2D,texture);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
 glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,2,2,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 glColor3f(1,1,1);glEnable(GL_ALPHA_TEST);glAlphaFunc(GL_GREATER,.5f);
 for(unsigned textured=0;textured<2;textured++){
  if(textured)glEnable(GL_TEXTURE_2D);else glDisable(GL_TEXTURE_2D);
  glBegin(GL_TRIANGLE_FAN);
  glTexCoord4d(0,0,0,1);glVertex2d(0,0);
  glTexCoord4d(1,0,0,1);glVertex2d(240,0);
  glTexCoord4d(1,1,0,1);glVertex2d(240,160);
  glTexCoord4d(0,1,0,1);glVertex2d(0,160);glEnd();
 }
 glFinish();int ok=glGetError()==GL_NO_ERROR;glDeleteTextures(1,&texture);
 glMatrixMode(GL_MODELVIEW);glPopMatrix();glMatrixMode(GL_PROJECTION);glPopMatrix();glPopAttrib();
 return ok;
}
