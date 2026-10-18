static unsigned long long source_suppressed_upload_calls;
__declspec(dllexport) unsigned long long nf_source_suppressed_upload_calls(void){return source_suppressed_upload_calls;}
static unsigned long long source_suppressed_raster_calls;
__declspec(dllexport) unsigned long long nf_source_suppressed_raster_calls(void){return source_suppressed_raster_calls;}

/* Isolated diagnostic command capture. Calls still execute original GL.
   Owned upload bytes, no framebuffer readback. Not yet a complete replay ABI. */
typedef struct {uint32_t opcode,argc;double args[12];uint64_t offset,bytes;} NFCommandRecord;
static NFCommandRecord *command_records;static uint8_t*command_payload;static size_t command_count,command_bytes;static unsigned command_active,command_error,command_unsupported;
#define NF_COMMAND_LIMIT 100000
#define NF_PAYLOAD_LIMIT (64u*1024u*1024u)
static void command_record(unsigned opcode,unsigned argc,const double*args,const void*payload,size_t bytes){
 if(!command_active)return;if(command_count==NF_COMMAND_LIMIT||bytes>NF_PAYLOAD_LIMIT-command_bytes){command_error=1;return;}
 NFCommandRecord*r=command_records+command_count++;memset(r,0,sizeof(*r));r->opcode=opcode;r->argc=argc;memcpy(r->args,args,argc*sizeof(double));r->offset=command_bytes;r->bytes=bytes;
 if(bytes){memcpy(command_payload+command_bytes,payload,bytes);command_bytes+=bytes;}
}
__declspec(dllexport) int nf_command_capture_open(void){if(command_active||command_records)return 1;command_records=calloc(NF_COMMAND_LIMIT,sizeof(*command_records));command_payload=malloc(NF_PAYLOAD_LIMIT);if(!command_records||!command_payload){free(command_records);free(command_payload);command_records=NULL;command_payload=NULL;return 2;}command_count=command_bytes=command_error=command_unsupported=0;command_active=1;return 0;}
__declspec(dllexport) int nf_command_capture_mark(uint64_t e,uint64_t g,uint64_t i){if(!command_active||e>9007199254740992ull||g>9007199254740992ull||i>9007199254740992ull)return 1;double a[3]={(double)e,(double)g,(double)i};command_record(1,3,a,NULL,0);return command_error;}
__declspec(dllexport) int nf_command_capture_end_frame(uint64_t e,uint64_t g,uint64_t i){if(!command_active||e>9007199254740992ull||g>9007199254740992ull||i>9007199254740992ull)return 1;double a[3]={(double)e,(double)g,(double)i};command_record(2,3,a,NULL,0);return command_error;}
__declspec(dllexport) int nf_command_capture_stats(uint64_t*out){if(!out)return 1;out[0]=command_count;out[1]=command_bytes;out[2]=command_error;out[3]=command_unsupported;out[4]=sizeof(NFCommandRecord);return 0;}
__declspec(dllexport) int nf_command_capture_copy(void*records,size_t n,void*payload,size_t bytes){if(!command_records||!records||n!=command_count*sizeof(NFCommandRecord)||bytes!=command_bytes||(bytes&&!payload))return 1;memcpy(records,command_records,n);if(bytes)memcpy(payload,command_payload,bytes);return command_error;}
__declspec(dllexport) void nf_command_capture_close(void){command_active=0;free(command_records);free(command_payload);command_records=NULL;command_payload=NULL;command_count=command_bytes=0;}
static void APIENTRY command_glBegin(GLenum mode){double ca_args[12]={mode};command_record(10,1,ca_args,NULL,0);source_suppressed_raster_calls++;}
static void APIENTRY command_glEnd(void){double ca_args[12]={0};command_record(11,0,ca_args,NULL,0);source_suppressed_raster_calls++;}
static void APIENTRY command_glVertex2d(GLdouble x,GLdouble y){double ca_args[12]={x,y};command_record(12,2,ca_args,NULL,0);source_suppressed_raster_calls++;}
static void APIENTRY command_glVertex2i(GLint x,GLint y){double ca_args[12]={x,y};command_record(13,2,ca_args,NULL,0);source_suppressed_raster_calls++;}
static void APIENTRY command_glTexCoord2i(GLint s,GLint t){double ca_args[12]={s,t};command_record(14,2,ca_args,NULL,0);glTexCoord2i(s,t);}
static void APIENTRY command_glTexCoord4d(GLdouble s,GLdouble t,GLdouble r,GLdouble q){double ca_args[12]={s,t,r,q};command_record(15,4,ca_args,NULL,0);glTexCoord4d(s,t,r,q);}
static void APIENTRY command_glColor4f(GLfloat r,GLfloat g,GLfloat b,GLfloat a){double ca_args[12]={r,g,b,a};command_record(16,4,ca_args,NULL,0);glColor4f(r,g,b,a);}
static void APIENTRY command_glColor3f(GLfloat r,GLfloat g,GLfloat b){double ca_args[12]={r,g,b};command_record(17,3,ca_args,NULL,0);glColor3f(r,g,b);}
static void APIENTRY command_glColor3ub(GLubyte r,GLubyte g,GLubyte b){double ca_args[12]={r,g,b};command_record(18,3,ca_args,NULL,0);glColor3ub(r,g,b);}
static void APIENTRY command_glEnable(GLenum cap){double ca_args[12]={cap};command_record(19,1,ca_args,NULL,0);glEnable(cap);}
static void APIENTRY command_glDisable(GLenum cap){double ca_args[12]={cap};command_record(20,1,ca_args,NULL,0);glDisable(cap);}
static void APIENTRY command_glScissor(GLint x,GLint y,GLsizei w,GLsizei h){double ca_args[12]={x,y,w,h};command_record(21,4,ca_args,NULL,0);glScissor(x,y,w,h);}
static void APIENTRY command_glBindTexture(GLenum target,GLuint texture){double ca_args[12]={target,texture};command_record(22,2,ca_args,NULL,0);glBindTexture(target,texture);}
static void APIENTRY command_glTexParameteri(GLenum target,GLenum name,GLint value){double ca_args[12]={target,name,value};command_record(23,3,ca_args,NULL,0);glTexParameteri(target,name,value);}
static void APIENTRY command_glBlendFunc(GLenum s,GLenum d){double ca_args[12]={s,d};command_record(24,2,ca_args,NULL,0);glBlendFunc(s,d);}
static void APIENTRY command_glAlphaFunc(GLenum fn,GLclampf ref){double ca_args[12]={fn,ref};command_record(25,2,ca_args,NULL,0);glAlphaFunc(fn,ref);}
static void APIENTRY command_glMatrixMode(GLenum mode){double ca_args[12]={mode};command_record(26,1,ca_args,NULL,0);glMatrixMode(mode);}
static void APIENTRY command_glLoadIdentity(void){double ca_args[12]={0};command_record(27,0,ca_args,NULL,0);glLoadIdentity();}
static void APIENTRY command_glOrtho(GLdouble l,GLdouble r,GLdouble b,GLdouble t,GLdouble n,GLdouble f){double ca_args[12]={l,r,b,t,n,f};command_record(28,6,ca_args,NULL,0);glOrtho(l,r,b,t,n,f);}
static void APIENTRY command_glPushMatrix(void){double ca_args[12]={0};command_record(29,0,ca_args,NULL,0);glPushMatrix();}
static void APIENTRY command_glPopMatrix(void){double ca_args[12]={0};command_record(30,0,ca_args,NULL,0);glPopMatrix();}
static void APIENTRY command_glPushAttrib(GLbitfield mask){double ca_args[12]={mask};command_record(31,1,ca_args,NULL,0);glPushAttrib(mask);}
static void APIENTRY command_glPopAttrib(void){double ca_args[12]={0};command_record(32,0,ca_args,NULL,0);glPopAttrib();}
static void APIENTRY command_glViewport(GLint x,GLint y,GLsizei w,GLsizei h){double ca_args[12]={x,y,w,h};command_record(33,4,ca_args,NULL,0);glViewport(x,y,w,h);}
static void APIENTRY command_glClear(GLbitfield mask){double ca_args[12]={mask};command_record(34,1,ca_args,NULL,0);glClear(mask);}
static void APIENTRY command_glClearColor(GLclampf r,GLclampf g,GLclampf b,GLclampf a){double ca_args[12]={r,g,b,a};command_record(35,4,ca_args,NULL,0);glClearColor(r,g,b,a);}
static void APIENTRY command_glPixelStorei(GLenum name,GLint value){double ca_args[12]={name,value};command_record(36,2,ca_args,NULL,0);glPixelStorei(name,value);}
static void APIENTRY command_glCopyTexImage2D(GLenum target,GLint level,GLenum fmt,GLint x,GLint y,GLsizei w,GLsizei h,GLint border){double ca_args[12]={target,level,fmt,x,y,w,h,border};command_record(37,8,ca_args,NULL,0);glCopyTexImage2D(target,level,fmt,x,y,w,h,border);}
static void APIENTRY command_glCopyTexSubImage2D(GLenum target,GLint level,GLint xo,GLint yo,GLint x,GLint y,GLsizei w,GLsizei h){double ca_args[12]={target,level,xo,yo,x,y,w,h};command_record(38,8,ca_args,NULL,0);source_suppressed_upload_calls++;}
static void APIENTRY command_glTexImage2D(GLenum target,GLint level,GLint internal,GLsizei w,GLsizei h,GLint border,GLenum fmt,GLenum type,const void*pixels){double a[8]={target,level,internal,w,h,border,fmt,type};size_t bytes=0;if(pixels){if(fmt==GL_RGBA&&type==GL_UNSIGNED_BYTE&&w>0&&h>0)bytes=(size_t)w*h*4;else if(command_active)command_unsupported++;}command_record(100,8,a,pixels,bytes);if(pixels)source_suppressed_upload_calls++;else glTexImage2D(target,level,internal,w,h,border,fmt,type,pixels);}
static void APIENTRY command_glTexSubImage2D(GLenum target,GLint level,GLint x,GLint y,GLsizei w,GLsizei h,GLenum fmt,GLenum type,const void*pixels){double a[8]={target,level,x,y,w,h,fmt,type};size_t bytes=0;if(pixels){if(fmt==GL_RGBA&&type==GL_UNSIGNED_BYTE&&w>0&&h>0)bytes=(size_t)w*h*4;else if(command_active)command_unsupported++;}command_record(101,8,a,pixels,bytes);source_suppressed_upload_calls++;}
#define glBegin command_glBegin
#define glEnd command_glEnd
#define glVertex2d command_glVertex2d
#define glVertex2i command_glVertex2i
#define glTexCoord2i command_glTexCoord2i
#define glTexCoord4d command_glTexCoord4d
#define glColor4f command_glColor4f
#define glColor3f command_glColor3f
#define glColor3ub command_glColor3ub
#define glEnable command_glEnable
#define glDisable command_glDisable
#define glScissor command_glScissor
#define glBindTexture command_glBindTexture
#define glTexParameteri command_glTexParameteri
#define glBlendFunc command_glBlendFunc
#define glAlphaFunc command_glAlphaFunc
#define glMatrixMode command_glMatrixMode
#define glLoadIdentity command_glLoadIdentity
#define glOrtho command_glOrtho
#define glPushMatrix command_glPushMatrix
#define glPopMatrix command_glPopMatrix
#define glPushAttrib command_glPushAttrib
#define glPopAttrib command_glPopAttrib
#define glViewport command_glViewport
#define glClear command_glClear
#define glClearColor command_glClearColor
#define glPixelStorei command_glPixelStorei
#define glCopyTexImage2D command_glCopyTexImage2D
#define glCopyTexSubImage2D command_glCopyTexSubImage2D
#define glTexImage2D command_glTexImage2D
#define glTexSubImage2D command_glTexSubImage2D


static void APIENTRY command_glGenTextures(GLsizei n,GLuint*ids){glGenTextures(n,ids);double a[1]={n};command_record(110,1,a,ids,n>0?(size_t)n*sizeof(GLuint):0);}
static void APIENTRY command_glDeleteTextures(GLsizei n,const GLuint*ids){double a[1]={n};command_record(111,1,a,ids,n>0?(size_t)n*sizeof(GLuint):0);glDeleteTextures(n,ids);}
#define glGenTextures command_glGenTextures
#define glDeleteTextures command_glDeleteTextures
static GLuint APIENTRY command_glCreateShader(GLenum type){GLuint(APIENTRY*fn)(GLenum type)=(void*)wglGetProcAddress("glCreateShader");GLuint value=fn(type);double a[12]={type,value};command_record(200,2,a,NULL,0);return value;}
static GLuint APIENTRY command_glCreateProgram(void){GLuint(APIENTRY*fn)(void)=(void*)wglGetProcAddress("glCreateProgram");GLuint value=fn();double a[12]={value};command_record(201,1,a,NULL,0);return value;}
static void APIENTRY command_glCompileShader(GLuint shader){void(APIENTRY*fn)(GLuint shader)=(void*)wglGetProcAddress("glCompileShader");double a[12]={shader};command_record(203,1,a,NULL,0);fn(shader);}
static void APIENTRY command_glAttachShader(GLuint program,GLuint shader){void(APIENTRY*fn)(GLuint program,GLuint shader)=(void*)wglGetProcAddress("glAttachShader");double a[12]={program,shader};command_record(204,2,a,NULL,0);fn(program,shader);}
static void APIENTRY command_glLinkProgram(GLuint program){void(APIENTRY*fn)(GLuint program)=(void*)wglGetProcAddress("glLinkProgram");double a[12]={program};command_record(205,1,a,NULL,0);fn(program);}
static void APIENTRY command_glUseProgram(GLuint program){void(APIENTRY*fn)(GLuint program)=(void*)wglGetProcAddress("glUseProgram");double a[12]={program};command_record(206,1,a,NULL,0);fn(program);}
static void APIENTRY command_glUniform1i(GLint location,GLint value){void(APIENTRY*fn)(GLint location,GLint value)=(void*)wglGetProcAddress("glUniform1i");double a[12]={location,value};command_record(208,2,a,NULL,0);fn(location,value);}
static void APIENTRY command_glUniform2f(GLint location,GLfloat x,GLfloat y){void(APIENTRY*fn)(GLint location,GLfloat x,GLfloat y)=(void*)wglGetProcAddress("glUniform2f");double a[12]={location,x,y};command_record(209,3,a,NULL,0);fn(location,x,y);}
static void APIENTRY command_glUniform4f(GLint location,GLfloat x,GLfloat y,GLfloat z,GLfloat w){void(APIENTRY*fn)(GLint location,GLfloat x,GLfloat y,GLfloat z,GLfloat w)=(void*)wglGetProcAddress("glUniform4f");double a[12]={location,x,y,z,w};command_record(210,5,a,NULL,0);fn(location,x,y,z,w);}
static void APIENTRY command_glActiveTexture(GLenum unit){void(APIENTRY*fn)(GLenum unit)=(void*)wglGetProcAddress("glActiveTexture");double a[12]={unit};command_record(211,1,a,NULL,0);fn(unit);}
static void APIENTRY command_glDeleteShader(GLuint shader){void(APIENTRY*fn)(GLuint shader)=(void*)wglGetProcAddress("glDeleteShader");double a[12]={shader};command_record(212,1,a,NULL,0);fn(shader);}
static void APIENTRY command_glDeleteProgram(GLuint program){void(APIENTRY*fn)(GLuint program)=(void*)wglGetProcAddress("glDeleteProgram");double a[12]={program};command_record(213,1,a,NULL,0);fn(program);}
static void APIENTRY command_glShaderSource(GLuint shader,GLsizei count,const char*const*strings,const GLint*lengths){
 void(APIENTRY*fn)(GLuint,GLsizei,const char*const*,const GLint*)=(void*)wglGetProcAddress("glShaderSource");
 if(command_active){size_t bytes=0;for(GLsizei i=0;i<count;i++){size_t n=lengths&&lengths[i]>=0?(size_t)lengths[i]:strlen(strings[i]);if(n>NF_PAYLOAD_LIMIT-bytes){command_error=1;break;}bytes+=n;}
  if(!command_error){char*text=malloc(bytes+1);if(!text)command_error=1;else{size_t at=0;for(GLsizei i=0;i<count;i++){size_t n=lengths&&lengths[i]>=0?(size_t)lengths[i]:strlen(strings[i]);memcpy(text+at,strings[i],n);at+=n;}text[bytes]=0;double a[2]={shader,count};command_record(202,2,a,text,bytes+1);free(text);}}}
 fn(shader,count,strings,lengths);
}
static GLint APIENTRY command_glGetUniformLocation(GLuint program,const char*name){GLint(APIENTRY*fn)(GLuint,const char*)=(void*)wglGetProcAddress("glGetUniformLocation");GLint location=fn(program,name);double a[2]={program,location};command_record(207,2,a,name,strlen(name)+1);return location;}
static PROC WINAPI command_wglGetProcAddress(LPCSTR name){PROC real=wglGetProcAddress(name);if(!real||(uintptr_t)real<=3||(intptr_t)real==-1)return real;
if(!strcmp(name,"glCreateShader"))return (PROC)command_glCreateShader;
if(!strcmp(name,"glCreateProgram"))return (PROC)command_glCreateProgram;
if(!strcmp(name,"glCompileShader"))return (PROC)command_glCompileShader;
if(!strcmp(name,"glAttachShader"))return (PROC)command_glAttachShader;
if(!strcmp(name,"glLinkProgram"))return (PROC)command_glLinkProgram;
if(!strcmp(name,"glUseProgram"))return (PROC)command_glUseProgram;
if(!strcmp(name,"glUniform1i"))return (PROC)command_glUniform1i;
if(!strcmp(name,"glUniform2f"))return (PROC)command_glUniform2f;
if(!strcmp(name,"glUniform4f"))return (PROC)command_glUniform4f;
if(!strcmp(name,"glActiveTexture"))return (PROC)command_glActiveTexture;
if(!strcmp(name,"glDeleteShader"))return (PROC)command_glDeleteShader;
if(!strcmp(name,"glDeleteProgram"))return (PROC)command_glDeleteProgram;
if(!strcmp(name,"glShaderSource"))return (PROC)command_glShaderSource;
if(!strcmp(name,"glGetUniformLocation"))return (PROC)command_glGetUniformLocation;
return real;}
#define wglGetProcAddress command_wglGetProcAddress
