#ifndef NF_MENU_RENDERER_GPU_H
#define NF_MENU_RENDERER_GPU_H
#include "hardware_submission.h"
/* Calling renderer thread owns current GL context; payload is immutable.
   Failure never authorizes presentation. Kind selection belongs to producer. */
int nf_menu_render_hardware(const NFHardwareSubmission*,int compose);
void nf_menu_renderer_destroy(void);
void nf_menu_renderer_stats(unsigned out[4]);
#endif
