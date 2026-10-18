package org.codex.nfsugpreview;
import android.util.AtomicFile;
import java.io.*;
import java.security.*;
final class PrivateStore {
 private final File root;
 PrivateStore(File root){this.root=root;}
 File file(String name){return new File(root,name);}
 byte[] read(String name,int limit)throws IOException{
  AtomicFile f=new AtomicFile(file(name));
  try(InputStream in=f.openRead();ByteArrayOutputStream out=new ByteArrayOutputStream()){
   byte[] buffer=new byte[8192];int n;
   while((n=in.read(buffer))!=-1){if(out.size()+n>limit)throw new IOException("Saved file exceeds limit");out.write(buffer,0,n);}
   return out.toByteArray();
  }catch(FileNotFoundException absent){return null;}
 }
 void write(String name,byte[] data)throws IOException{
  if(data==null)return;
  AtomicFile f=new AtomicFile(file(name));FileOutputStream out=null;
  try{out=f.startWrite();out.write(data);f.finishWrite(out);}
  catch(IOException e){if(out!=null)f.failWrite(out);throw e;}
 }
 void importRom(InputStream input)throws Exception{
  ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[32768];int n;
  MessageDigest sha=MessageDigest.getInstance("SHA-256");
  while((n=input.read(b))!=-1){if(out.size()+n>32*1024*1024)throw new IOException("ROM exceeds 32 MB");out.write(b,0,n);sha.update(b,0,n);}
  StringBuilder hash=new StringBuilder();for(byte v:sha.digest())hash.append(String.format("%02x",v&255));
  if(!hash.toString().equals("53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593"))
   throw new IOException("Please select the supplied USA/Europe NFS Underground GBA ROM");
  write("game.gba",out.toByteArray());
 }
}
