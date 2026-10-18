package org.codex.nfsugpreview;
/** One pending immutable scene; lifecycle generations reject work captured before a reset. */
final class NativePresentation {
 static final class Frame {
  final long generation,epoch,refresh;final NativeRetainedScene scene;
  private final byte[] original;
  Frame(long g,long e,long r,byte[] pixels,NativeRetainedScene s){generation=g;epoch=e;refresh=r;original=pixels.clone();scene=s;}
  byte[] original(){return original.clone();}
 }
 private long generation,epoch=-1,refresh=-1;private boolean enabled,active;private Frame latest;
 synchronized void enabled(boolean value){if(enabled!=value){enabled=value;invalidate();}}
 synchronized boolean enabled(){return enabled;}
 synchronized void active(boolean value){if(active!=value){active=value;invalidate();}}
 synchronized void invalidate(){generation++;epoch=refresh=-1;latest=null;}
 synchronized long token(){return generation;}
 synchronized Frame latest(){return enabled&&active?latest:null;}
 synchronized boolean current(Frame frame){return frame!=null&&frame==latest&&enabled&&active&&frame.generation==generation;}
 // A newer same-generation frame may arrive while the GPU works. Rejecting it
 // solely for replacement can starve presentation forever on a slower device.
 synchronized boolean canPresent(Frame frame){return frame!=null&&enabled&&active&&frame.generation==generation&&frame.epoch==epoch&&frame.refresh<=refresh;}
 synchronized boolean publish(long token,long e,long r,byte[] pixels,NativeRetainedScene scene){
  if(token!=generation||!enabled||!active)return false;
  if(pixels==null||pixels.length!=153600||e<=0||r<0)throw new IllegalArgumentException("Presentation identity");
  if(scene!=null&&(scene.epoch!=e||scene.refresh!=r))throw new IllegalArgumentException("Presentation scene identity");
  if(epoch!=-1&&(e!=epoch||r<=refresh))throw new IllegalArgumentException("Presentation ordering");
  latest=new Frame(generation,e,r,pixels,scene);epoch=e;refresh=r;return true;
 }
}
