#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <string.h>
#include <windows.h>
#include <psapi.h>
static __thread uint64_t residency[5];
static int resident_pages(void*data,size_t size,uint64_t*out){
 SYSTEM_INFO info;GetSystemInfo(&info);size_t page=info.dwPageSize;uintptr_t first=(uintptr_t)data & ~(uintptr_t)(page-1);size_t count=(((uintptr_t)data+size-1)-first)/page+1;
 if(count>4097)return 0;PSAPI_WORKING_SET_EX_INFORMATION*rows=calloc(count,sizeof(*rows));if(!rows)return 0;
 for(size_t i=0;i<count;i++)rows[i].VirtualAddress=(void*)(first+i*page);
 int ok=QueryWorkingSetEx(GetCurrentProcess(),rows,(DWORD)(count*sizeof(*rows)));uint64_t valid=0;
 if(ok)for(size_t i=0;i<count;i++)valid+=rows[i].VirtualAttributes.Valid?1:0;
 free(rows);out[0]=count;out[1]=valid;return ok;
}
static __thread uint64_t prepared_stats[7];
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
 ok=read(epoch,refresh,NULL,0,&needed);
 Py_END_ALLOW_THREADS
 if(!ok||needed<40||needed>0x1000000){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Unavailable or oversized owned frame");return NULL;}
 if(needed>(size_t)PyBytes_GET_SIZE(packet)){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Private storage capacity exceeded");return NULL;}
 uintptr_t before=(uintptr_t)PyBytes_AS_STRING(packet);LARGE_INTEGER a,b,f;QueryPerformanceFrequency(&f);QueryPerformanceCounter(&a);
 if(_PyBytes_Resize(&packet,(Py_ssize_t)needed)<0)return NULL;
 QueryPerformanceCounter(&b);prepared_stats[0]=before!=(uintptr_t)PyBytes_AS_STRING(packet);prepared_stats[1]=b.QuadPart-a.QuadPart;prepared_stats[2]=f.QuadPart;
 if(!resident_pages(PyBytes_AS_STRING(packet),needed,prepared_stats+3)){Py_DECREF(packet);PyErr_SetString(PyExc_RuntimeError,"Residency query failed");return NULL;}
 char*data=PyBytes_AS_STRING(packet);
 Py_BEGIN_ALLOW_THREADS
 QueryPerformanceCounter(&a);ok=read(epoch,refresh,data,needed,&written);QueryPerformanceCounter(&b);prepared_stats[5]=b.QuadPart-a.QuadPart;prepared_stats[6]=needed;
 Py_END_ALLOW_THREADS
 if(!ok||written!=needed){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Owned frame capture failed");return NULL;}
 uint32_t h[6];uint64_t e,t;memcpy(h,data,24);memcpy(&e,data+24,8);memcpy(&t,data+32,8);
 if(h[0]!=0x3346474e||h[1]!=refresh||e!=epoch||t!=(uint64_t)refresh*280896||h[4]!=76800||h[5]!=76800||40ULL+h[2]+h[3]+h[4]+h[5]!=needed){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Unpaired owned frame header");return NULL;}
 return packet;
}
static PyObject* stats(PyObject*self,PyObject*ignored){return Py_BuildValue("(KKKKKKK)",prepared_stats[0],prepared_stats[1],prepared_stats[2],prepared_stats[3],prepared_stats[4],prepared_stats[5],prepared_stats[6]);}
static PyMethodDef methods[]={{"stats",stats,METH_NOARGS,"Shrink relocation and pre-read residency."},{"prepare",prepare,METH_VARARGS,"Prepare sole-owned unpublished storage."},{"capture",capture,METH_VARARGS,"Capture into unpublished private immutable storage."},{NULL,NULL,0,NULL}};
static struct PyModuleDef module={PyModuleDef_HEAD_INIT,"_owned_frame_capture_prepared_profile_candidate",NULL,-1,methods};
PyMODINIT_FUNC PyInit__owned_frame_capture_prepared_profile_candidate(void){return PyModule_Create(&module);}

