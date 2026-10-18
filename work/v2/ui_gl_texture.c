#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <GL/gl.h>
#include <limits.h>
#include "ui_gl_texture.h"

int nf_ui_gl_texture_upload_rgba(const uint32_t *pixels, uint32_t width,
                                 uint32_t height, uint32_t *handle) {
    if (!pixels || !width || !height || width > INT_MAX || height > INT_MAX || !handle)
        return 0;
    *handle = 0;
    while (glGetError() != GL_NO_ERROR) { }
    GLuint id = 0;
    glGenTextures(1, &id);
    if (!id) return 0;
    glBindTexture(GL_TEXTURE_2D, id);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, (GLsizei)width, (GLsizei)height,
                 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels);
    if (glGetError() != GL_NO_ERROR) {
        glDeleteTextures(1, &id);
        return 0;
    }
    *handle = (uint32_t)id;
    return 1;
}

void nf_ui_gl_texture_delete(uint32_t handle) {
    GLuint id = (GLuint)handle;
    if (id) glDeleteTextures(1, &id);
}
