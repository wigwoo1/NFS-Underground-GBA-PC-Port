#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <string.h>
typedef int (*Reader)(uint64_t,unsigned,void*,size_t,size_t*);
static PyObject* capture(PyObject*self,PyObject*args){
 unsigned long long address,epoch;unsigned refresh;
 if(!PyArg_ParseTuple(args,"KKI",&address,&epoch,&refresh))return NULL;
 if(!address||!epoch){PyErr_SetString(PyExc_ValueError,"Invalid reader identity");return NULL;}
 Reader read=(Reader)(uintptr_t)address;size_t needed=0,written=0;
 if(!read(epoch,refresh,NULL,0,&needed)||needed<40||needed>0x1000000){PyErr_SetString(PyExc_ValueError,"Unavailable or oversized owned frame");return NULL;}
 PyObject*packet=PyBytes_FromStringAndSize(NULL,(Py_ssize_t)needed);if(!packet)return NULL;
 char*data=PyBytes_AS_STRING(packet);
 if(!read(epoch,refresh,data,needed,&written)||written!=needed){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Owned frame capture failed");return NULL;}
 uint32_t h[6];uint64_t e,t;memcpy(h,data,24);memcpy(&e,data+24,8);memcpy(&t,data+32,8);
 if(h[0]!=0x3346474e||h[1]!=refresh||e!=epoch||t!=(uint64_t)refresh*280896||h[4]!=76800||h[5]!=76800||40ULL+h[2]+h[3]+h[4]+h[5]!=needed){Py_DECREF(packet);PyErr_SetString(PyExc_ValueError,"Unpaired owned frame header");return NULL;}
 return packet;
}
static PyMethodDef methods[]={{"capture",capture,METH_VARARGS,"Capture into unpublished private immutable storage."},{NULL,NULL,0,NULL}};
static struct PyModuleDef module={PyModuleDef_HEAD_INIT,"_owned_frame_capture_candidate",NULL,-1,methods};
PyMODINIT_FUNC PyInit__owned_frame_capture_candidate(void){return PyModule_Create(&module);}
