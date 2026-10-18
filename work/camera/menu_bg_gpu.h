/* Source bitmap assets only. BG2 affine lookup runs per physical fragment. */
static const char*menu_bg_fragment=
"#version 120\n"
"uniform sampler2D indices,palette;uniform vec4 affine;uniform vec2 origin;uniform float enabled;"
"void main(){vec2 cell=floor((vec2(gl_FragCoord.x,2160.0-gl_FragCoord.y)-vec2(300.0,0.0))/13.5);"
"if(enabled<0.5||cell.x<0.0||cell.x>=240.0||cell.y<0.0||cell.y>=160.0){gl_FragColor=vec4(0.0);return;}"
"vec2 s=floor((origin+vec2(affine.x,affine.z)*cell.x)/256.0);"
"if(s.x<0.0||s.y<0.0||s.x>=240.0||s.y>=160.0){gl_FragColor=vec4(0.0);return;}"
"float index=floor(texture2D(indices,(s+vec2(0.5))/vec2(240.0,160.0)).r*255.0+0.5);"
"gl_FragColor=index<0.5?vec4(0.0):texture2D(palette,vec2((index+0.5)/256.0,0.5));}";
