#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <string.h>
#include <windows.h>
static __thread uint64_t profile[7];
static uint64_t tick(void){LARGE_INTEGER t;QueryPerformanceCounter(&t);return t.QuadPart;}
static uint64_t cycles(void){ULONG64 t=0;QueryThreadCycleTime(GetCurrentThread(),&t);return t;}
static void reset_profile(void){memset(profile,0,sizeof(profile));LARGE_INTEGER f;QueryPerformanceFrequency(&f);profile[0]=f.QuadPart;}
static PyObject* stats(PyObject*self,PyObject*ignored){return Py_BuildValue("(KKKKKKK)",profile[0],profile[1],profile[2],profile[3],profile[4],profile[5],profile[6]);}

typedef struct {PyObject* packet;} Prepared;
static void destroy_prepared(PyObject* capsule){Prepared*p=PyCapsule_GetPointer(capsule,"nf.private.frame");if(p){Py_XDECREF(p->packet);PyMem_Free(p);}}
static PyObject* prepare(PyObject*self,PyObject*args){
 Py_ssize_t size;if(!PyArg_ParseTuple(args,"n",&size))return NULL;
 if(size<40||size>0x1000000){PyErr_SetString(PyExc_ValueError,"Invalid private capacity");return NULL;}
 Prepared*p=PyMem_Calloc(1,sizeof(*p));if(!p)return PyErr_NoMemory();
 p->packet=PyBytes_FromStringAndSize(NULL,size);if(!p->packet){PyMem_Free(p);return NULL;}
 char*data=PyBytes_AS_STRING(p->packet);
 Py_BEGIN_ALLOW_THREADS
 memset(data,0,(size_t)size);
 Py_END_ALLOW_THREADS
 PyObject*out=PyCapsule_New(p,"nf.private.frame",destroy_prepared);
 if(!out){Py_DECREF(p->packet);PyMem_Free(p);}return out;
}
typedef int (*Reader)(uint64_t,unsigned,void*,size_t,size_t*);
static PyObject* frame_size(PyObject*self,PyObject*args){
 unsigned long long address,epoch;unsigned refresh;
 if(!PyArg_ParseTuple(args,"KKI",&address,&epoch,&refresh))return NULL;
 if(!address||!epoch){PyErr_SetString(PyExc_ValueError,"Invalid reader identity");return NULL;}
 size_t needed=0;int ok;
 Py_BEGIN_ALLOW_THREADS
 reset_profile();profile[1]=tick();uint64_t qc=cycles();ok=((Reader)(uintptr_t)address)(epoch,refresh,NULL,0,&needed);profile[3]=cycles()-qc;profile[2]=tick();
 Py_END_ALLOW_THREADS
 if(!ok||needed<40||needed>0x1000000){PyErr_SetString(PyExc_ValueError,"Invalid frame size");return NULL;}
 return PyLong_FromSize_t(needed);
}
static PyObject* capture(PyObject*self,PyObject*args){
 unsigned long long address,epoch;unsigned refresh;PyObject*capsule;
 if(!PyArg_ParseTuple(args,"OKKI",&capsule,&address,&epoch,&refresh))return NULL;
 if(!address||!epoch){PyErr_SetString(PyExc_ValueError,"Invalid reader identity");return NULL;}
 Prepared*prepared=PyCapsule_GetPointer(capsule,"nf.private.frame");if(!prepared)return NULL;
 if(!prepared->packet){PyErr_SetString(PyExc_ValueError,"Private storage already consumed");return NULL;}
 PyObject*packet=prepared->packet;prepared->packet=NULL;
 Reader read=(Reader)(uintptr_t)address;size_t needed=0,written=0;
 int ok;
 Py_BEGIN_ALLOW_THREADS
 reset_profile();profile[1]=tick();uint64_t qc=cycles();ok=read(epoch,refresh,NULL,0,&needed);profile[3]=cycles()-qc;profile[2]=tick();
 Py_END_ALLOW_THREADS
 if(!ok||needed<40||needed>0x1000000){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Unavailable or oversized owned frame");return NULL;}
 if(needed>(size_t)PyBytes_GET_SIZE(packet)){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Private storage capacity exceeded");return NULL;}
 if(_PyBytes_Resize(&packet,(Py_ssize_t)needed)<0)return NULL;
 char*data=PyBytes_AS_STRING(packet);
 Py_BEGIN_ALLOW_THREADS
 profile[4]=tick();uint64_t cc=cycles();ok=read(epoch,refresh,data,needed,&written);profile[6]=cycles()-cc;profile[5]=tick();
 Py_END_ALLOW_THREADS
 if(!ok||written!=needed){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Owned frame capture failed");return NULL;}
 uint32_t h[6];uint64_t e,t;memcpy(h,data,24);memcpy(&e,data+24,8);memcpy(&t,data+32,8);
 if(h[0]!=0x3346474e||h[1]!=refresh||e!=epoch||t!=(uint64_t)refresh*280896||h[4]!=76800||h[5]!=76800||40ULL+h[2]+h[3]+h[4]+h[5]!=needed){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Unpaired owned frame header");return NULL;}
 return packet;
}
static PyMethodDef methods[]={{"stats",stats,METH_NOARGS,"Native query/copy wall ticks and cycles."},{"frame_size",frame_size,METH_VARARGS,"Validated current frame size query."},{"prepare",prepare,METH_VARARGS,"Prepare sole-owned unpublished storage."},{"capture",capture,METH_VARARGS,"Capture into unpublished private immutable storage."},{NULL,NULL,0,NULL}};
static struct PyModuleDef module={PyModuleDef_HEAD_INIT,"_owned_frame_capture_exact_timed",NULL,-1,methods};
PyMODINIT_FUNC PyInit__owned_frame_capture_exact_timed(void){return PyModule_Create(&module);}

