#include "owned_d3d_region_read_candidate.c"
static unsigned sky_diag_enabled,sky_diag_ready;
static unsigned char sky_diag_pixels[640*16*4];
__declspec(dllexport) int nf_d3d_sky_diag_enable(unsigned enabled){if(!valid()||enabled>1)return 37;sky_diag_enabled=enabled;sky_diag_ready=0;return 0;}
__declspec(dllexport) int nf_d3d_source_sky_diag_batch(void*info,void*copy){sky_diag_ready=0;int rc=nf_d3d_source_sky_pan_batch(info,copy);if(rc||!sky_diag_enabled)return rc;rc=nf_d3d_read_region(1600,600,640,16,sky_diag_pixels,sizeof(sky_diag_pixels));if(!rc)sky_diag_ready=1;return rc;}
__declspec(dllexport) int nf_d3d_sky_diag_copy(void*out,size_t bytes){if(!valid()||!sky_diag_ready||!out||bytes!=sizeof(sky_diag_pixels))return 37;memcpy(out,sky_diag_pixels,bytes);sky_diag_ready=0;return 0;}
