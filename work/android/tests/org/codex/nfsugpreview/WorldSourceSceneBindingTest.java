package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.util.*;
public final class WorldSourceSceneBindingTest {
 private static void ok(boolean v,String why){if(!v)throw new AssertionError(why);}
 private static byte[] bytes(ByteBuffer b){byte[] a=new byte[b.remaining()];b.get(a);return a;}
 private static void rejected(Runnable call){boolean bad=false;try{call.run();}catch(IllegalArgumentException expected){bad=true;}ok(bad,"Forged source owner accepted");}
 public static void main(String[] args)throws Exception{
  Path dir=Paths.get(args[0]);int fixtures=0,whole=0,split=0,forgeries=0;boolean atomic=false;
  try(DirectoryStream<Path> paths=Files.newDirectoryStream(dir,"display-*.nab")){for(Path path:paths){
   byte[] original=Files.readAllBytes(path);NativeSceneSnapshot display=new NativeSceneSnapshot(original);NativeSourceSceneBinding binding=new NativeSourceSceneBinding();int[] requests={0};List<byte[]> returned=new ArrayList<>();
   NativeSourceSceneBinding.Source provider=(epoch,serial,begin,end)->{ok(epoch==display.epoch,"Epoch request");requests[0]++;try{byte[] data=Files.readAllBytes(dir.resolve("source-"+serial+".nsp"));returned.add(data);return data;}catch(Exception e){throw new RuntimeException(e);}};
   NativeSceneSnapshot result=binding.bind(display,provider);ok(result!=null&&requests[0]==display.geometryCount(),"Exact owner request count");
   ok(result.epoch==display.epoch&&result.refresh==display.refresh&&result.kind==display.kind&&result.splitRow==display.splitRow,"Display identity changed");
   ok(Arrays.equals(bytes(result.packedLayers()),bytes(display.packedLayers()))&&Arrays.equals(bytes(result.provenance()),bytes(display.provenance())),"Historical ownership changed");
   for(int i=0;i<result.geometryCount();i++)ok(Arrays.equals(bytes(result.geometry(i).data()),Files.readAllBytes(dir.resolve("source-"+display.geometry(i).serial+".nsp"))),"Wrong source bytes");
   byte[] owned=bytes(result.data());for(byte[] raw:returned)Arrays.fill(raw,(byte)0);Arrays.fill(original,(byte)0);ok(Arrays.equals(owned,bytes(result.data())),"Caller memory alias");
   NativeSceneSnapshot repeated=binding.bind(display,(e,s,b,n)->{throw new AssertionError("Immutable owner cache missed");});ok(Arrays.equals(owned,bytes(repeated.data())),"Repeated bind changed output");
   binding.clear();requests[0]=0;ok(binding.bind(display,provider)!=null&&requests[0]==display.geometryCount(),"Clear did not invalidate cache");
   for(int field=0;field<4;field++){
    final int f=field;rejected(()->new NativeSourceSceneBinding().bind(display,(e,s,b,n)->{try{byte[] raw=Files.readAllBytes(dir.resolve("source-"+s+".nsp"));ByteBuffer value=ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);int at=16+f*4;value.putInt(at,f==3?value.getInt(at)^1:value.getInt(at)+1);return raw;}catch(Exception ex){throw new RuntimeException(ex);}}));forgeries++;
   }
   byte[] changed=bytes(display.data());ByteBuffer header=ByteBuffer.wrap(changed).order(ByteOrder.LITTLE_ENDIAN);long epoch=display.epoch+1;header.putLong(24,epoch);int provenance=(int)header.getLong(112);header.putLong(provenance,epoch);for(int i=0;i<2;i++){int at=provenance+64+i*64;if(header.getLong(at+56)==1)header.putLong(at,epoch);}
   NativeSceneSnapshot nextEpoch=new NativeSceneSnapshot(changed);int[] staleCalls={0};ok(binding.bind(nextEpoch,(e,s,b,n)->{staleCalls[0]++;return null;})==null&&staleCalls[0]==1,"Cached geometry crossed epoch");
   ok(new NativeSourceSceneBinding().bind(display,(e,s,b,n)->null)==null,"Missing source accepted");
   if(display.kind==2&&!atomic){NativeSourceSceneBinding partial=new NativeSourceSceneBinding();long newer=display.geometry(1).serial;ok(partial.bind(display,(e,s,b,n)->s==newer?null:provider.packet(e,s,b,n))==null,"Partial split published");requests[0]=0;ok(partial.bind(display,provider)!=null&&requests[0]==2,"Failed split polluted cache");atomic=true;}
   fixtures++;if(display.kind==1)whole++;else split++;
  }}
  ok(fixtures==11&&whole>0&&split>0&&atomic,"Fixture scope");System.out.println("PASS_SOURCE_DISPLAY_BINDING fixtures="+fixtures+" whole="+whole+" split="+split+" forged_owners="+forgeries+" immutable_cache_epoch_reset_atomic_split=PASS");
 }
}
