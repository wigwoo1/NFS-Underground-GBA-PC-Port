"""Reproduce timing-report inconsistency; does not modify production or run Android."""
from pathlib import Path
import argparse, hashlib, json, subprocess, tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project',type=Path,default=Path('Y:/CODEX/NFSUG-Native-PC-Port'))
args=parser.parse_args();root=args.project
base=Path('C:/NFSUG-Workspace')
jdk=base/'android-tools/jdk-21.0.12.1+1/bin'
source=root/'work/android/java/org/codex/nfsugpreview/NativeWorkProfile.java'
witness=root/'work/android/capture/ProfileSnapshotWitness.java'
instrumentation=root/'work/android/instrumentation/org/codex/nfsugpreview/LivePresentationInstrumentation.java'
session=root/'work/android/java/org/codex/nfsugpreview/GameSession.java'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p) for p in [source,witness,instrumentation,session]}
dest=root/'outputs/nfsug-native-renderer/camera-research/profile-snapshot-witness-20261017'
dest.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='profile-witness-',dir=base) as temporary:
    folder=Path(temporary).resolve();assert folder.parent==base.resolve() and folder.name.startswith('profile-witness-')
    # Explicit files compile the actual production class, not a copied implementation.
    compile_run=subprocess.run([str(jdk/'javac.exe'),'--release','8','-d',str(folder),str(source),str(witness)],capture_output=True,text=True,timeout=40)
    (dest/'compile.log').write_text(compile_run.stdout+compile_run.stderr,encoding='utf-8')
    compile_run.check_returncode()
    run=subprocess.run([str(jdk/'java.exe'),'-cp',str(folder),'org.codex.nfsugpreview.ProfileSnapshotWitness'],capture_output=True,text=True,timeout=40)
    (dest/'run.log').write_text(run.stdout+run.stderr,encoding='utf-8');run.check_returncode()
    report=json.loads(run.stdout)
assert report['result']=='PASS_UNCHANGED_PROFILE_SNAPSHOT_WITNESS'
assert report['mixed_completed_read_cases']==report['inflight_nested_cases']==200
assert report['quiescent_counts_balanced'] and not report['production_code_modified']
assert all(sha(Path(path))==digest for path,digest in inputs.items())
report.update(source_sha256=inputs,runner_sha256=sha(Path(__file__)),
    conclusion='Both mixed sequential observations and inflight nested work can violate nested<=outer. An atomic metrics copy alone does not exclude inflight work.',
    next_dependency='Implement completed-work accounting or safely quiesce relevant producers before sampling. Preserve game timing, ownership/generation guards and strict analyzer; re-run real Android GPU/UI/profile acceptance.',
    limits='Controlled host JVM schedules, no Android runtime or game core/GPU/audio. Establishes mechanisms allowed by current class, not exclusive cause of prior emulator result. This is diagnostic evidence, not a third attempted production fix.')
for path in [source,witness]:
    data=path.read_bytes();(dest/path.name).write_bytes(data)
    assert sha(dest/path.name)==sha(path)
(dest/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
entry='''

2026-10-17 — Unchanged profile counter failure mechanisms deterministically reproduced
Previous turn PROGRESS: firstRe-imagined artworkdraft saved with honestsub4Klimit. Returned to primary performance dependency with DIAGNOSTIC ONLY; no thirdfix attempted. Re-read current NativeWorkProfile,LivePresentationInstrumentation reportloop,GameSession outerfinally. Added ProfileSnapshotWitness.java and run_profile_snapshot_witness.py under work/android/capture. Compiled exact unchanged NativeWorkProfile onJDK21 withJava8target (deprecationwarningsonly).400 controlledworker/latch cases PASS:200 reportreads separatedbyanotherfullyfinishedcapture yielded outer1/nested2 while finalactualcounts2/2;200 stoppedafter nestedtimerfinish/beforeouterfinish yielded outer1/nested2 withNOwritesduringobservation. Allquiescentcounterpairsbalanced. No sleeps/randomrace timing,5secondbarriertimeouts,workerexceptionspropagated/joined.
This PROVES both failuremechanisms possible undercurrentcounterAPI. It does NOT prove exclusivecause ofpriorAndroid27>26. It adds concreteconstraint: anatomicallstagecopyALONEwouldstillincludeunfinishednestedwork andcannotguaranteecompleted-capturecohort. Nextfixneedsfinished-workaccounting orsafeproducerdrain,thenstrictanalyzer andactualGPU/live/UIregressions. DoNOTrelaxnested<=outergate orreadrawmeansasverifiedranking.
Archived sourceSHA-bound report,unchangedproductionclass snapshot,Javawitness,compile/runlogs under camera-research/profile-snapshot-witness-20261017. Runnerchecksall4inputsourceSHAbefore/after. HostJVM componentdiagnostic only; noAndroidAPK/game/core/GL/audioexecution, no productionedits or playablepackageupdates. ROM/saves/stablefallback untouched. Prior twofocusedfixattemptstop remains. MODELUPGRADERECOMMENDED currentassumedLuna ->SolMedium forcompleted-workcoherence implementation andtimingverification; canreturnLunaLowafterboundedregressionspass. Goalactive,no pause/completion/newtask/automation. OverallPARTIALLYVERIFIED rough73%unchanged; nativeportseparatefrom4Ksyncemulatorfallback;fullscene60/fullrace/audio/device/texturemenu remainopen. Noactivejobs.
'''
status=root/'outputs/nfsug-native-renderer/camera-research/STATUS.md'
with status.open('a',encoding='utf-8') as stream:stream.write(entry)
assert entry in status.read_text(encoding='utf-8')
print(json.dumps(report,indent=2))
