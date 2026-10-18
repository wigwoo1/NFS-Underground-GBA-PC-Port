package org.codex.nfsugpreview;
import android.os.Bundle;import java.io.File;
/** Instrumentation-only storage isolation; all UI/lifecycle behavior inherited unchanged. */
public final class FixturePreviewActivity extends PreviewActivity {
 static volatile FixturePreviewActivity current;
 static volatile String TEST_ROOT="preview-ui-test-private";
 @Override public File getFilesDir(){return new File(super.getFilesDir(),TEST_ROOT);}
 @Override public void onCreate(Bundle state){super.onCreate(state);current=this;}
}
