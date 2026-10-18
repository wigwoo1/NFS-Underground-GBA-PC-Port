/* A valid pair crossing a model boundary is unavailable, not fatal.
   Packet validation, allocation and graphics failures remain fatal. */
static int preview_render_available(NFSnapshotStore*s,double target,char**args,int*ready,int*incompatible){
 *incompatible=0;
 if(!*ready)return 0;
 int result=render_packet_at(s,target,args);
 if(result==24){*ready=0;*incompatible=1;return 0;}
 return result;
}
