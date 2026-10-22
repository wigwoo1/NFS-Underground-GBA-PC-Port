"""Use this launcher for Codex tests; refuse unknown audible test binaries."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys

VERIFIED_SESSION_MUTE_HOSTS={'01cff14a8cfb5e524a8fabd7e7f659df1c4ce8beaffe6738c108e5b1f3aea3c6'}

def run_muted_test(exe,args,timeout=90):
    exe=Path(exe)
    no_audio='--no-audio' in args
    digest=hashlib.sha256(exe.read_bytes()).hexdigest()
    if not no_audio:
        if digest not in VERIFIED_SESSION_MUTE_HOSTS:
            raise RuntimeError('Refusing potentially audible test: use a verified muted test host or --no-audio.')
        args=list(args)
        if '--mute-audio' not in args:args.append('--mute-audio')
    r=subprocess.run([str(exe),*args],capture_output=True,text=True,timeout=timeout)
    if r.returncode:raise RuntimeError(f'Test exited {r.returncode}: {r.stdout}\n{r.stderr}')
    if not no_audio:
        if '--report' not in args:raise RuntimeError('Muted audio tests require a report destination.')
        d=json.loads(Path(args[args.index('--report')+1]).read_text())
        if not (d['audio_device_opened'] and d['test_audio_mute_requested'] and d['test_audio_mute_verified'] and d['test_audio_mute_sessions']>0 and d['test_audio_mute_checks']>0 and d['test_audio_mute_failures']==0 and d['test_audio_mute_restored']):
            raise RuntimeError('Silent audio-device test did not satisfy its mute/restore checks.')
    return r

def run_no_audio_launcher_test(launcher,env,timeout=60):
    """Verify the known package CMD's explicit no-audio branch before running it."""
    launcher=Path(launcher)
    text=launcher.read_text()
    for required in ['if "%~1"=="--verify-launch" (','set "VERIFY=--frames 60 --hidden --fast --no-audio"','--report "%~dp0last-run.json" %VERIFY%']:
        if required not in text:raise RuntimeError('Launcher lacks the audited no-audio verification branch.')
    r=subprocess.run([env['COMSPEC'],'/d','/c','call',str(launcher),'--verify-launch'],capture_output=True,text=True,env=env,timeout=timeout)
    if r.returncode:raise RuntimeError(f'No-audio launcher failed: {r.stdout}\n{r.stderr}')
    d=json.loads((launcher.parent/'last-run.json').read_text())
    if d['audio_device_opened']:raise RuntimeError('Launcher verification unexpectedly opened an audio device.')
    return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',required=True)
    parser.add_argument('--timeout',type=int,default=90)
    options,args=parser.parse_known_args()
    if args[:1]==['--']:args=args[1:]
    result=run_muted_test(options.exe,args,options.timeout)
    print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
