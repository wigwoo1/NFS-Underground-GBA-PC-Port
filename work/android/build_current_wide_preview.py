"""Current native preview build: explicit verified64-entry capture ABI. Tests/package separate."""
from pathlib import Path
import argparse,json,subprocess,sys
parser=argparse.ArgumentParser()
for name in ['toolchain','ndk','ninja','cmake','core-build','output','keystore']:parser.add_argument('--'+name,type=Path,required=True)
args=parser.parse_args();source=Path(__file__).resolve().parent;native=args.output/'native'
subprocess.run([sys.executable,str(source/'capture/build_capture.py'),'--output',str(native),'--ndk',str(args.ndk),'--ninja',str(args.ninja),'--cmake',str(args.cmake),'--core-build',str(args.core_build),'--jni','--visibility-capacity','64'],check=True)
report=json.loads((native/'capture-jni-build-report.json').read_text());assert report['visibility_capacity']==64 and report['jni'] and not report.get('diagnostic_only',False)
subprocess.run([sys.executable,str(source/'build_android_apk.py'),'--toolchain',str(args.toolchain),'--native-root',str(args.core_build),'--capture-native-root',str(native),'--output',str(args.output/'production'),'--keystore',str(args.keystore)],check=True)
print('BUILT_CURRENT_WIDE_NATIVE_PREVIEW_RUNTIME_TESTS_REQUIRED')
