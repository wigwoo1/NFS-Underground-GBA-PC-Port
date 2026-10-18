package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;
/** Independent established Java reader oracle for native PC source-color ports. */
public final class PcBackgroundReferenceExport {
 static void save(Path path,ByteBuffer buffer)throws Exception{byte[] data=new byte[buffer.remaining()];buffer.get(data);Files.write(path,data);}
 public static void main(String[] args)throws Exception{Path input=Paths.get(args[0]),out=Paths.get(args[1]);Files.createDirectories(out);int scenes=0;try(DirectoryStream<Path> paths=Files.newDirectoryStream(input,"source-race-background-*.nrb")){for(Path path:paths){NativeBackgroundScene frame=new NativeBackgroundScene(Files.readAllBytes(path));String name=Long.toString(frame.sky.scene.refresh);save(out.resolve(name+".background.rgba"),frame.exactRgba());save(out.resolve(name+".palette.rgba"),NativeHistoricalPalette.rgba(frame.sky.scene));save(out.resolve(name+".sky.rgba"),frame.sky.exactRgba());scenes++;}}if(scenes!=9)throw new AssertionError("Missing reference scope");System.out.println("PASS_PC_BACKGROUND_JAVA_REFERENCE scenes=9");}
}
