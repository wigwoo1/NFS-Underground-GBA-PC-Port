from pathlib import Path
p=Path('work/camera');emitter=(p/'source_triangle_packet_candidate.c').read_text().replace('count>32','count>64').replace('polygon[64][5]','polygon[128][5]')
(p/'source_triangle_packet_integration_candidate.h').write_text(emitter)
s=(p/'owned_gpu_source_command_capture_state_candidate.c').read_text();pos=s.index('static void anchor_transform')
helper='''#include "source_triangle_packet_integration_candidate.h"
static int source_packet_gl(const double*polygon,unsigned count,double cx,double cy,double scale){
 double output[3780],projection[3]={cx,cy,scale},color[4]={1,1,1,1};unsigned written=0;
 if(nf_source_triangle_packet(polygon,count,projection,color,output,378,&written))return 0;
 glBegin(GL_TRIANGLES);for(unsigned j=0;j<written;j++){const double*v=output+j*10;glTexCoord4d(v[2],v[3],v[4],v[5]);glVertex2d(v[0],v[1]);}glEnd();return 1;
}
'''
s=s[:pos]+helper+s[pos:]
old='glBegin(GL_TRIANGLE_FAN);for(unsigned j=0;j<n;j++){double q=1/polygon[j][2];glTexCoord4d(polygon[j][3]*q,polygon[j][4]*q,0,q);glVertex2d(120+128*polygon[j][0]*q,87+128*polygon[j][1]*q);}glEnd();'
assert s.count(old)==2;s=s.replace(old,'if(!source_packet_gl(&polygon[0][0],n,120,87,128))return 0;')
old='glBegin(GL_TRIANGLE_FAN);for(unsigned j=0;j<clipped;j++){double q=1/polygon[j][2];glTexCoord4d(polygon[j][3]*q,polygon[j][4]*q,0,q);glVertex2d(center[0]+scale*polygon[j][0]*q,center[1]+scale*polygon[j][1]*q);}glEnd();'
assert old in s;s=s.replace(old,'if(!source_packet_gl(&polygon[0][0],clipped,center[0],center[1],scale))return 0;')
(p/'owned_gpu_source_packet_integration_candidate.c').write_text(s)
s=(p/'test_source_command_capture_state_pixels.py').read_text().replace('owned-gpu-source-command-capture-state-candidate.dll','owned-gpu-source-packet-integration-candidate.dll').replace('source-command-state-records.bin','source-packet-integration-records.bin').replace('source-command-state-payload.bin','source-packet-integration-payload.bin')
(p/'test_source_packet_integration_candidate.py').write_text(s)
