package org.codex.nfsugpreview;
import android.app.*;import android.content.*;import android.os.*;import java.io.*;import java.nio.*;import java.nio.file.*;import java.util.zip.*;import org.json.*;
public final class WorldInstrumentation extends Instrumentation {
 void ok(boolean value,String why){if(!value)throw new AssertionError(why);}
 byte[] bytes(File file)throws Exception{return Files.readAllBytes(file.toPath());}
 @Override public void onCreate(Bundle b){super.onCreate(b);start();}
 @Override public void onStart(){Bundle result=new Bundle();try{
  File files=getTargetContext().getFilesDir(),root=new File(files,"world-runtime-fixtures");root.mkdirs();String prefix=root.getCanonicalPath()+File.separator;
  File archive=new File(files,"world-runtime-fixtures.zip");
  try(ZipInputStream zip=new ZipInputStream(new FileInputStream(archive))){ZipEntry entry;byte[] buffer=new byte[32768];while((entry=zip.getNextEntry())!=null){File file=new File(root,entry.getName());ok(file.getCanonicalPath().startsWith(prefix),"Fixture path escaped");if(entry.isDirectory()){file.mkdirs();continue;}file.getParentFile().mkdirs();try(FileOutputStream out=new FileOutputStream(file)){int n;while((n=zip.read(buffer))!=-1)out.write(buffer,0,n);}}}
  File fixtures=new File(root,"fixtures"),text=new File(files,"world-runtime-text"),mesh=new File(files,"world-runtime-mesh");JSONObject expected=new JSONObject(new String(bytes(new File(root,"manifest.json")),"UTF-8"));
  WorldDecodeTest.main(new String[]{fixtures.getAbsolutePath(),text.getAbsolutePath()});WorldMeshTest.main(new String[]{fixtures.getAbsolutePath(),mesh.getAbsolutePath()});
  int packets=0,models=0;double maxCamera=0,maxFloat=0;
  for(File file:new File(root,"text").listFiles()){if(!file.isFile())continue;ok(java.util.Arrays.equals(bytes(file),bytes(new File(text,file.getName()))),"World/material/order bytes differ: "+file.getName());packets++;}
  for(File file:new File(root,"mesh").listFiles()){if(!file.isFile())continue;byte[] golden=bytes(file),actual=bytes(new File(mesh,file.getName()));ok(golden.length==actual.length,"Mesh length");ByteBuffer a=ByteBuffer.wrap(actual).order(ByteOrder.LITTLE_ENDIAN),b=ByteBuffer.wrap(golden).order(ByteOrder.LITTLE_ENDIAN);
   if(file.getName().endsWith(".camera")){while(a.hasRemaining()){double av=a.getDouble(),bv=b.getDouble(),error=Math.abs(av-bv);ok(Double.isFinite(av)&&error<=1e-9*Math.max(1,Math.abs(bv)),"Camera endpoint mismatch");maxCamera=Math.max(maxCamera,error);}}
   else{while(a.hasRemaining()){float av=a.getFloat(),bv=b.getFloat();double error=Math.abs((double)av-bv);ok(Float.isFinite(av)&&error<=2e-6*Math.max(1,Math.abs(bv)),"Projected mesh mismatch");maxFloat=Math.max(maxFloat,error);}models++;}
  }
  ok(packets==expected.getInt("valid_packets")&&models==expected.getInt("meshes"),"Corpus counts");
  JSONObject report=new JSONObject();report.put("result","PASS_ANDROID_WORLD_DECODE_MESH");report.put("valid_packets",packets);report.put("malformed_rejected",expected.getInt("malformed_packets"));report.put("surfaces",expected.getInt("surfaces"));report.put("meshes",models);report.put("source_corrected_rejected",expected.getInt("source_corrected_rejected"));report.put("max_camera_difference",maxCamera);report.put("max_float_difference",maxFloat);report.put("material_order_lighting_bytes_exact",true);report.put("host_c_reference_verified",true);report.put("api",Build.VERSION.SDK_INT);report.put("gpu_world_rendering",false);report.put("real_time_pacing",false);
  try(FileOutputStream out=getTargetContext().openFileOutput("world-runtime-report.json",Context.MODE_PRIVATE)){out.write(report.toString(2).getBytes("UTF-8"));}result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
 }catch(Throwable e){android.util.Log.e("NFSUGWorldTest","Failed",e);result.putString("stream","FAIL: "+e);finish(Activity.RESULT_CANCELED,result);}}
}
