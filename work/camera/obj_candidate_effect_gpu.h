#ifndef NF_OBJ_CANDIDATE_EFFECT_GPU_H
#define NF_OBJ_CANDIDATE_EFFECT_GPU_H
/* Resolved candidate color and metadata must be separate: transparent higher
   priority OBJ texels can change flags without replacing the retained color.
   Candidate textures use the original 240x160 grid, top-down, nearest sampled.
   Metadata blue byte: bit7 prepared, bit6 backdrop effect control, low6 visible
   window controls. Unprepared inputs retain unrestricted controls. This pass
   does not resolve OAM overlap or brightness preprocessing itself. */
static const char*obj_candidate_effect_fragment=
"#version 120\n"
"uniform sampler2D candidateColor,candidateMetadata,nativeBackground,ownedText,ownedTextDistance;uniform int ownedTextEnabled,ownedTextSdfEnabled;"
"uniform vec4 backdropColor,effectParameters,firstTargets,secondTargets,coefficients;"
"vec4 parameters;"
NF_OBJ_EFFECT_VARIANT_GLSL
"void main(){vec2 screen=vec2(gl_FragCoord.x,2160.0-gl_FragCoord.y);"
"vec2 cell=floor((screen-vec2(300.0,0.0))/13.5);"
"vec2 uv=(cell+vec2(0.5))/vec2(240.0,160.0);"
"vec4 objectColor=vec4(0.0);vec4 metadata=vec4(0.0);"
"if(cell.x>=0.0&&cell.x<240.0&&cell.y>=0.0&&cell.y<160.0){objectColor=texture2D(candidateColor,uv);metadata=texture2D(candidateMetadata,uv);}"
"float flags=floor(metadata.b*255.0+0.5);bool prepared=flags>=128.0;float control=prepared?mod(flags,64.0):63.0;float effects=mod(floor(control/32.0),2.0);float backdropEffects=prepared?mod(floor(flags/64.0),2.0):1.0;"
"parameters=vec4(effects>0.5?effectParameters.x:0.0,floor(metadata.g*255.0+0.5),floor(metadata.r*255.0+0.5),effectParameters.w);"
"objectColor.rgb*=255.0;vec4 backgroundColor=texture2D(nativeBackground,gl_FragCoord.xy/vec2(3840.0,2160.0));backgroundColor.rgb*=255.0;"
"if(ownedTextEnabled!=0&&cell.x>=0.0&&cell.x<240.0&&cell.y>=0.0&&cell.y<160.0){vec4 textColor=texture2D(ownedText,uv);if(ownedTextSdfEnabled!=0){vec2 grid=(screen-vec2(300.0,0.0))/13.5;float distance=(texture2D(ownedTextDistance,(grid+vec2(0.5))/vec2(240.0,160.0)).r*255.0-128.0)/16.0;float coverage=clamp(0.5+distance,0.0,1.0);if(coverage>0.0){backgroundColor.rgb=mix(backgroundColor.rgb,textColor.rgb*255.0,coverage);backgroundColor.a=1.0;}}else if(textColor.a>0.5)backgroundColor=vec4(textColor.rgb*255.0,1.0);}"
"backgroundColor.a*=mod(floor(control/4.0),2.0);if(mod(floor(control/16.0),2.0)<0.5)objectColor.a=0.0;"
NF_OBJ_EFFECT_BODY_GLSL_IMPL("prepared")
"if(!hasObj&&!hasBg&&effectParameters.x>1.5&&firstTargets.z>0.5&&effects!=backdropEffects){parameters.x=effectParameters.x;gl_FragColor=vec4(variant(floor(backdropColor.rgb+vec3(0.5)),backdropEffects)/255.0,1.0);}"
"}";

#endif
