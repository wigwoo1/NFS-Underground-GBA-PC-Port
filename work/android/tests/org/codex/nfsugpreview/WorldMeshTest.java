package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;
public final class WorldMeshTest {
 public static void main(String[] args)throws Exception{Path input=Paths.get(args[0]),output=Paths.get(args[1]);Files.createDirectories(output);int meshes=0,rejected=0;
  try(java.nio.file.DirectoryStream<Path> files=Files.newDirectoryStream(input,"*.nsp")){for(Path file:files){if(file.getFileName().toString().startsWith("bad-"))continue;NativeScenePacket packet=new NativeScenePacket(1,Files.readAllBytes(file));NativeWorldScene world=new NativeWorldScene(packet);
   for(int i=0;i<world.surfaceCount();i++){if(world.surface(i).sourceAttributes()!=null)continue;boolean unsupported=false;try{NativeWorldMesh mesh=new NativeWorldMesh(packet,world,i);if(unsupported)throw new AssertionError("Flattened corrected road");DoubleBuffer camera=mesh.cameraVertices();ByteBuffer c=ByteBuffer.allocate(camera.remaining()*8).order(ByteOrder.LITTLE_ENDIAN);while(camera.hasRemaining())c.putDouble(camera.get());Files.write(output.resolve(file.getFileName()+"-"+i+".camera"),c.array());FloatBuffer vertices=mesh.vertices();ByteBuffer v=ByteBuffer.allocate(vertices.remaining()*4).order(ByteOrder.LITTLE_ENDIAN);while(vertices.hasRemaining())v.putFloat(vertices.get());Files.write(output.resolve(file.getFileName()+"-"+i+".mesh"),v.array());if(mesh.vertices().hasRemaining())try{mesh.vertices().put(0,0);throw new AssertionError();}catch(ReadOnlyBufferException good){}meshes++;}catch(IllegalArgumentException expected){if(!unsupported)throw expected;rejected++;}}
  }}System.out.println("PASS_WORLD_MESH meshes="+meshes+" source_corrected_rejected="+rejected);
 }
}
