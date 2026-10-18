from pathlib import Path
import shutil,zipfile
out=Path('outputs/nfsug-research');src=Path('work/package/NFSUG-Port-Lab-source');src.mkdir(parents=True,exist_ok=True)
for folder in ['vendor','tests','tools']:(src/folder).mkdir(exist_ok=True)
for name in ['native_span.c','native_span.h','controller.h','README.md','ENGINE-NOTES.md']:
 shutil.copy2(out/name,src/name)
for original,name in [('host.c','main.c'),('probe.c','bridge.c')]:
 text=Path('work',original).read_text().replace('../outputs/nfsug-research/','').replace('work/span-cycles.csv','span-cycles.csv')
 (src/name).write_text(text)
shutil.copy2('work/mgba.zip',src/'vendor/mgba-0.10.5.zip')
shutil.copy2('work/mgba-0.10.5/LICENSE',out/'mGBA-LICENSE.txt');shutil.copy2(out/'mGBA-LICENSE.txt',src/'vendor/mGBA-LICENSE.txt')
test=Path('work/test_controller.c').read_text().replace('../outputs/nfsug-research/controller.h','../controller.h')
(src/'tests/test_controller.c').write_text(test)
test=Path('work/test_native.py').read_text()
test=test.replace("sys.path.insert(0,str(Path('work/pydeps').resolve()))",'')
test=test.replace("rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()","if len(sys.argv)!=2: raise SystemExit('Usage: python tests/test_native.py path/to/game.gba')\nrom=Path(sys.argv[1]).read_bytes()\nassert __import__('hashlib').sha256(rom).hexdigest()=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593'")
test=test.replace("Path('work/native_span.dll')","Path('build/native_span.dll')").replace("Path('outputs/nfsug-research/native-tests.json')","Path('build/native-tests.json')")
(src/'tests/test_native.py').write_text(test)
(src/'requirements-research.txt').write_text('capstone==5.0.9\nunicorn==2.1.4\nPillow>=11\n')
shutil.copy2('work/source-Build.ps1',src/'Build.ps1')
shutil.copy2('work/research_cli.py',src/'tools/research_cli.py')
(src/'BUILDING.md').write_text('''# Build and reproduce

Requirements: Windows x64, a MinGW-w64 C compiler, CMake 3.5 or later, PowerShell. The mGBA source archive is included; building does not download or include the game ROM.

From this directory:

```powershell
./Build.ps1 -CompilerBin 'C:/path/to/w64devkit/bin' -CmakeExe 'C:/path/to/cmake.exe'
./build/NFSUG-Port-Lab.exe --rom 'G:/path/to/your/game.gba'
```

The script can also discover CMake/gcc on PATH and includes the already discovered local toolchain as a fallback. It builds the host, research bridge DLL, isolated native routine DLL, and runs the controller tests. Source changes to the mGBA instruction dispatcher are applied explicitly by Build.ps1 to the included unmodified upstream archive. Original MPL notices are retained.

Optional reverse-engineering checks use Python 3.12+:

```powershell
python -m pip install -r requirements-research.txt
python tests/test_native.py 'G:/path/to/your/game.gba'
python tools/research_cli.py 'G:/path/to/your/game.gba' --frames 600
```

Use F5 in the host to create a snapshot. The research tool accepts `--state path/to/progress.state`, `--keys 1` (held accelerator), and `--native` to compare the recovered routine. It saves a screenshot, page-flip cadence, memory dumps, and binary span/polygon records under build/capture. Running it will overwrite earlier files in that capture directory.

`NFSUG-Port-Lab.exe --test 600 --native --state path/to/progress.state` performs a hidden graphics smoke test. Its report is written beside the executable. This test does not prove visible smoothness, 60-fps game updates, physical controller input, or audible quality.

The native routine is only a first migration step; see ENGINE-NOTES.md for its contract and known timing limits.
''')
with zipfile.ZipFile(out/'NFSUG-Port-Lab-source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in src.rglob('*'):
  if p.is_file() and not any(x in ('build','deps') for x in p.relative_to(src).parts):z.write(p,p.relative_to(src.parent))
shutil.copy2('work/native-driving.png',out/'gameplay-native-span.png')
print('Packaged',len(list(src.rglob('*'))),'entries')
