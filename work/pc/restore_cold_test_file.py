"""Restore one archived scratch artifact by its original absolute C: path."""
from pathlib import Path
import argparse,hashlib,json,shutil
parser=argparse.ArgumentParser();parser.add_argument('--path',required=True);args=parser.parse_args()
base=Path('C:/NFSUG-Workspace').resolve();project=Path('Y:/CODEX/NFSUG-Native-PC-Port');audit=project/'outputs/nfsug-native-renderer/camera-research/disk-cleanup-20261017-current'
target=Path(args.path).resolve();assert target.is_relative_to(base) and target.relative_to(base).parts[0].lower().startswith('nfsug')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
matches=[]
for ledger in ['removed-files.jsonl','binary-removed-files.jsonl']:
 p=audit/ledger
 if p.exists():
  for line in p.read_text().splitlines():
   r=json.loads(line)
   if Path(r['source']).resolve()==target:matches.append(r)
assert len(matches)==1,'No unique archived record for requested path';r=matches[0];source=Path(r['archive'])
assert source.resolve().is_relative_to((project/'cold-storage/c-scratch-20261017').resolve()) and sha(source)==r['sha256']
if target.exists():assert sha(target)==r['sha256'];print('Already present and exact')
else:
 assert shutil.disk_usage('C:/').free>r['bytes']+1024**3,'Keep at least1GiB free'
 target.parent.mkdir(parents=True,exist_ok=True);temp=target.with_suffix(target.suffix+'.restore-partial');assert not temp.exists()
 shutil.copyfile(source,temp);assert sha(temp)==r['sha256'];temp.rename(target);print('Restored',target)
