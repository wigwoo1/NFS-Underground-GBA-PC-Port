package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;
public final class ModelMeshTest {
 static void check(boolean value){if(!value)throw new AssertionError();}
 static void reject(byte[] model,int offset,int value){byte[] bad=model.clone();ByteBuffer.wrap(bad).order(ByteOrder.LITTLE_ENDIAN).putInt(offset,value);try{new NativeModelMesh(ByteBuffer.wrap(bad));throw new AssertionError("Accepted malformed model");}catch(IllegalArgumentException good){}}
 public static void main(String[] args)throws Exception{
  Path input=Paths.get(args[0]),out=Paths.get(args[1]);Files.createDirectories(out);int cases=0,triangles=0;
  try(java.nio.file.DirectoryStream<Path> files=Files.newDirectoryStream(input,"*.nfm")){for(Path file:files){byte[] raw=Files.readAllBytes(file);NativeModelMesh mesh=new NativeModelMesh(ByteBuffer.wrap(raw));DoubleBuffer camera=mesh.cameraVertices();ByteBuffer points=ByteBuffer.allocate(camera.remaining()*8).order(ByteOrder.LITTLE_ENDIAN);while(camera.hasRemaining())points.putDouble(camera.get());Files.write(out.resolve(file.getFileName()+".camera"),points.array());FloatBuffer vertices=mesh.vertices();ByteBuffer projected=ByteBuffer.allocate(vertices.remaining()*4).order(ByteOrder.LITTLE_ENDIAN);while(vertices.hasRemaining())projected.putFloat(vertices.get());Files.write(out.resolve(file.getFileName()+".mesh"),projected.array());
   ByteBuffer texture=mesh.texture();byte[] pixels=new byte[texture.remaining()];texture.get(pixels);Files.write(out.resolve(file.getFileName()+".rgba"),pixels);check(mesh.texture().position()==0);try{mesh.vertices().put(0,0);throw new AssertionError();}catch(ReadOnlyBufferException good){}ArraysFill(raw);check(mesh.texture().remaining()==mesh.width*mesh.height*4);
   byte[] original=Files.readAllBytes(file);reject(original,0,0);reject(original,4,2049);reject(original,8,513);reject(original,12,4097);reject(original,16,0);byte[] nan=original.clone();ByteBuffer.wrap(nan).order(ByteOrder.LITTLE_ENDIAN).putDouble(160,Double.NaN);try{new NativeModelMesh(ByteBuffer.wrap(nan));throw new AssertionError();}catch(IllegalArgumentException good){}
   cases++;triangles+=mesh.triangleVertices/3;
  }}check(cases>0);System.out.println("PASS_NATIVE_MODEL_MESH cases="+cases+" triangles="+triangles+" malformed="+(cases*6));
 }
 static void ArraysFill(byte[] raw){java.util.Arrays.fill(raw,(byte)165);}
}
