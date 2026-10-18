"""Reject invalid input and changed final RAM without touching the real session."""
from pathlib import Path
import json,csv,subprocess,sys,uuid
source=Path(sys.argv[1]).resolve();session=json.loads(source.read_text(encoding='utf-8-sig'))
prefix=source.parent/('negative-'+uuid.uuid4().hex);records=[]
for case in ('invalid-button-mask','changed-final-ram','wrong-source-clock','wrong-source-epoch','missing-hud-frame'):
    candidate=dict(session);manifest=Path(str(prefix)+'-'+case+'.json')
    if case=='invalid-button-mask':
        rows=list(csv.DictReader(Path(session['input_trace']).open()));rows[0]['keys']='1024'
        trace=Path(str(prefix)+'-input.csv')
        with trace.open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        candidate['input_trace']=str(trace)
    elif case=='changed-final-ram':
        candidate['ram_prefix']=str(prefix)+'-ram'
        for name in ('ewram','iwram'):
            data=bytearray(Path(session['ram_prefix']+'-'+name+'.bin').read_bytes())
            if name=='ewram':data[0]^=1
            Path(candidate['ram_prefix']+'-'+name+'.bin').write_bytes(data)
    elif case in ('wrong-source-clock','wrong-source-epoch'):
        rows=list(csv.DictReader(Path(session['display_trace']).open()))
        if case=='wrong-source-clock':rows[1]['target']=str(float(rows[1]['target'])+.01)
        else:next(row for row in rows if int(row['ready']))['epoch_mismatch']='1'
        trace=Path(str(prefix)+'-'+case+'-display.csv')
        with trace.open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        candidate['display_trace']=str(trace)
    else:
        import re
        log=Path(str(prefix)+'-missing-hud.log')
        log.write_text(re.sub(r'\bhud_drawn=\d+','hud_drawn=0',Path(session['log']).read_text(encoding='utf-8-sig')))
        candidate['log']=str(log)
    manifest.write_text(json.dumps(candidate))
    run=subprocess.run([sys.executable,str(Path(__file__).with_name('verify_prototype_session.py')),str(manifest)],capture_output=True,text=True)
    report=json.loads(manifest.with_name(manifest.stem+'-verification.json').read_text())
    assert run.returncode!=0 and report['result']=='FAIL',case
    if case=='changed-final-ram':assert report['error']=='ewram replay mismatch'
    records.append(dict(case=case,rejected=True))
report=dict(result='PASS',records=records,scope='Negative copies only; invalid mask, changed final RAM, altered original source-clock rate, wrong source epoch and missing HUD frame rejected. Real recorded session/ROM/state untouched.')
Path(__file__).with_name('prototype-session-rejection-tests.json').write_text(json.dumps(report,indent=2));print(report)
