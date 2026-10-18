#include "owned_d3d_region_read_candidate.c"
static unsigned sky_diag_enabled,sky_diag_ready,phase_ready;
static unsigned phase_valid[2];static double phase_weights[2];static unsigned char phase_planes[2][153600];
static unsigned char sky_diag_pixels[3840*16*4];
__declspec(dllexport) int nf_d3d_sky_diag_enable(unsigned enabled){if(!valid()||enabled>1)return 37;sky_diag_enabled=enabled;sky_diag_ready=0;phase_ready=0;return 0;}
__declspec(dllexport) int nf_d3d_source_sky_diag_batch(void*info,void*copy){sky_diag_ready=0;phase_ready=0;if(sky_diag_enabled){if(!valid()||!info||!copy)return 37;if(((SkyInfo)info)(phase_valid,phase_weights))return 37;for(unsigned i=0;i<2;i++){if(phase_valid[i]!=1||((PlaneCopy)copy)(i,phase_planes[i],153600))return 37;}phase_ready=1;}int rc=nf_d3d_source_sky_pan_batch(info,copy);if(rc||!sky_diag_enabled)return rc;rc=nf_d3d_read_region(0,600,3840,16,sky_diag_pixels,sizeof(sky_diag_pixels));if(!rc)sky_diag_ready=1;return rc;}
__declspec(dllexport) int nf_d3d_sky_diag_copy(void*out,size_t bytes){if(!valid()||!sky_diag_ready||!out||bytes!=sizeof(sky_diag_pixels))return 37;memcpy(out,sky_diag_pixels,bytes);sky_diag_ready=0;return 0;}

__declspec(dllexport) int nf_d3d_sky_phase_copy(unsigned slot,void*out,size_t bytes,double*weight){if(!valid()||!phase_ready||slot>1||!out||!weight||bytes!=153600)return 37;memcpy(out,phase_planes[slot],bytes);*weight=phase_weights[slot];return 0;}
