#ifndef NFSUG_UI_GL_TEXTURE_H
#define NFSUG_UI_GL_TEXTURE_H
#include <stdint.h>

/* Create one linear RGBA8 replacement texture on the caller's current GL
   context. The handle is published only after a successful upload. */
int nf_ui_gl_texture_upload_rgba(const uint32_t *pixels, uint32_t width,
                                 uint32_t height, uint32_t *handle);
void nf_ui_gl_texture_delete(uint32_t handle);

#endif
