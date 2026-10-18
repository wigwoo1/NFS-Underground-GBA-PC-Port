/* Native-background input must be a separate retained GPU texture; never
   sample the destination attachment while writing the HUD result. */
static const char*obj_textured_effect_fragment=
"#version 120\n"
"uniform sampler2D spriteAsset,nativeBackground;uniform vec4 backdropColor,parameters,firstTargets,secondTargets,coefficients,sourceRectangle;"
NF_OBJ_EFFECT_VARIANT_GLSL
"void main(){vec2 screen=vec2(gl_FragCoord.x,2160.0-gl_FragCoord.y);vec2 uv=(screen-sourceRectangle.xy)/sourceRectangle.zw;vec4 objectColor=texture2D(spriteAsset,uv);objectColor.rgb*=255.0;vec4 backgroundColor=texture2D(nativeBackground,gl_FragCoord.xy/vec2(3840.0,2160.0));backgroundColor.rgb*=255.0;"
NF_OBJ_EFFECT_BODY_GLSL "}";
