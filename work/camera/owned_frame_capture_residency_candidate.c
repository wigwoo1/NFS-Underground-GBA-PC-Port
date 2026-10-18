#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
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
static __thread uint64_t profile[15];
static uint64_t tick(void){LARGE_INTEGER t;QueryPerformanceCounter(&t);return t.QuadPart;}
static uint64_t cycles(void){ULONG64 t=0;QueryThreadCycleTime(GetCurrentThread(),&t);return t;}
#include <string.h>
typedef int (*Reader)(uint64_t,unsigned,void*,size_t,size_t*);
static PyObject* capture(PyObject*self,PyObject*args){
 unsigned long long address,epoch;unsigned refresh;
 if(!PyArg_ParseTuple(args,"KKI",&address,&epoch,&refresh))return NULL;
 if(!address||!epoch){PyErr_SetString(PyExc_ValueError,"Invalid reader identity");return NULL;}
 memset(profile,0,sizeof(profile));LARGE_INTEGER frequency;QueryPerformanceFrequency(&frequency);profile[12]=frequency.QuadPart;profile[0]=tick();
 Reader read=(Reader)(uintptr_t)address;size_t needed=0,written=0;
 int ok;
 Py_BEGIN_ALLOW_THREADS
 profile[1]=tick();uint64_t qc=cycles();ok=read(epoch,refresh,NULL,0,&needed);profile[13]=cycles()-qc;profile[2]=tick();
 Py_END_ALLOW_THREADS
 profile[3]=tick();
 if(!ok||needed<40||needed>0x1000000){PyErr_SetString(PyExc_ValueError,"Unavailable or oversized owned frame");return NULL;}
 profile[4]=tick();PyObject*packet=PyBytes_FromStringAndSize(NULL,(Py_ssize_t)needed);if(!packet)return NULL;
 profile[5]=tick();char*data=PyBytes_AS_STRING(packet);
 memset(residency,0,sizeof(residency));residency[0]=needed;
 if(!resident_pages(data,needed,residency+1)){Py_DECREF(packet);PyErr_SetString(PyExc_RuntimeError,"Residency query failed");return NULL;}
 Py_BEGIN_ALLOW_THREADS
 profile[6]=tick();uint64_t rc=cycles();ok=read(epoch,refresh,data,needed,&written);profile[14]=cycles()-rc;profile[7]=tick();
 Py_END_ALLOW_THREADS
 profile[8]=tick();
 if(!resident_pages(data,needed,residency+3)){Py_DECREF(packet);PyErr_SetString(PyExc_RuntimeError,"Residency query failed");return NULL;}
 if(!ok||written!=needed){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Owned frame capture failed");return NULL;}
 uint32_t h[6];uint64_t e,t;memcpy(h,data,24);memcpy(&e,data+24,8);memcpy(&t,data+32,8);
 if(h[0]!=0x3346474e||h[1]!=refresh||e!=epoch||t!=(uint64_t)refresh*280896||h[4]!=76800||h[5]!=76800||40ULL+h[2]+h[3]+h[4]+h[5]!=needed){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Unpaired owned frame header");return NULL;}
 profile[9]=tick();profile[10]=needed;profile[11]=written;return packet;
}
static PyObject* last_profile(PyObject*self,PyObject*ignored){PyObject*out=PyTuple_New(15);if(!out)return NULL;for(int i=0;i<15;i++){PyObject*v=PyLong_FromUnsignedLongLong(profile[i]);if(!v){Py_DECREF(out);return NULL;}PyTuple_SET_ITEM(out,i,v);}return out;}
static PyObject* last_residency(PyObject*self,PyObject*ignored){return Py_BuildValue("(KKKKK)",residency[0],residency[1],residency[2],residency[3],residency[4]);}
static PyMethodDef methods[]={{"last_residency",last_residency,METH_NOARGS,"Private output page residency before/after capture."},{"capture",capture,METH_VARARGS,"Capture into unpublished private immutable storage."},{"last_profile",last_profile,METH_NOARGS,"Calling thread last capture profile."},{NULL,NULL,0,NULL}};
static struct PyModuleDef module={PyModuleDef_HEAD_INIT,"_owned_frame_capture_residency_candidate",NULL,-1,methods};
PyMODINIT_FUNC PyInit__owned_frame_capture_residency_candidate(void){return PyModule_Create(&module);}

