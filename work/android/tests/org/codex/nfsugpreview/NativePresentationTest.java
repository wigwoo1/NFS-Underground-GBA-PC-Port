package org.codex.nfsugpreview;
import java.util.concurrent.*;import java.util.concurrent.atomic.*;
public final class NativePresentationTest {
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 static void reject(Runnable r){try{r.run();throw new AssertionError("Invalid identity accepted");}catch(IllegalArgumentException expected){}}
 public static void main(String[] args)throws Exception{
  NativePresentation box=new NativePresentation();byte[] pixels=new byte[153600];
  check(!box.publish(box.token(),1,1,pixels,null));box.enabled(true);check(!box.publish(box.token(),1,1,pixels,null));box.active(true);
  check(box.publish(box.token(),1,1,pixels,null));NativePresentation.Frame first=box.latest();pixels[0]=4;check(first.original()[0]==0);byte[] copied=first.original();copied[0]=9;check(first.original()[0]==0);
  check(box.publish(box.token(),1,2,pixels,null));check(!box.current(first));check(box.canPresent(first));check(box.current(box.latest()));
  reject(()->box.publish(box.token(),1,2,pixels,null));reject(()->box.publish(box.token(),2,3,pixels,null));reject(()->box.publish(box.token(),1,3,new byte[1],null));
  long old=box.token();box.active(false);check(box.latest()==null);check(!box.canPresent(first));box.active(true);check(!box.publish(old,1,3,pixels,null));check(box.publish(box.token(),2,1,pixels,null));
  old=box.token();box.enabled(false);check(box.latest()==null);box.enabled(true);check(!box.publish(old,2,2,pixels,null));
  final long captured=box.token();CountDownLatch ready=new CountDownLatch(1),resume=new CountDownLatch(1);AtomicBoolean staleAccepted=new AtomicBoolean(true);Thread worker=new Thread(()->{ready.countDown();try{resume.await();staleAccepted.set(box.publish(captured,3,1,pixels,null));}catch(Exception e){throw new RuntimeException(e);}});worker.start();ready.await();box.invalidate();resume.countDown();worker.join();check(!staleAccepted.get()&&box.latest()==null);
  AtomicReference<Throwable> failure=new AtomicReference<>();Thread producer=new Thread(()->{try{long token=box.token();for(int i=1;i<=10000;i++)check(box.publish(token,4,i,pixels,null));}catch(Throwable e){failure.set(e);}});producer.start();long observed=0;while(producer.isAlive()){NativePresentation.Frame frame=box.latest();if(frame!=null){check(frame.refresh>=observed);observed=frame.refresh;}}producer.join();if(failure.get()!=null)throw new AssertionError(failure.get());check(box.latest().refresh==10000);box.invalidate();check(box.latest()==null);check(!box.canPresent(first));
  System.out.println("PASS_NATIVE_PRESENTATION replacement_frames=10000 stale_inflight_rejected=true pause_mode_epoch_guards=true immutable_fallback=true");
 }
}
