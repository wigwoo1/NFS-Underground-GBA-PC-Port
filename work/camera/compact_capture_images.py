"""Lossless compaction of one explicitly selected diagnostic capture prefix."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
p=Path(__file__).resolve().parent
prefix=Path(sys.argv[1]).resolve();root=(p/'prototype-runs').resolve()
assert prefix.parent==root and prefix.name.startswith('threaded-prepared-')
records=[]
for source in sorted(root.glob(prefix.name+'-*.ppm')):
    raw=source.read_bytes();im=Image.open(source);im.load()
    assert im.mode=='RGB' and im.size==(3840,2160)
    pixels=im.tobytes();target=source.with_suffix('.png');assert not target.exists()
    im.save(target)
    with Image.open(target) as check:assert check.mode==im.mode and check.size==im.size and check.tobytes()==pixels
    records.append(dict(source=str(source),source_sha256=hashlib.sha256(raw).hexdigest(),source_bytes=len(raw),
        lossless_png=str(target),png_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),rgb_sha256=hashlib.sha256(pixels).hexdigest()))
    # Only verified generated diagnostic image; source packets/palettes preserved.
    source.unlink()
report=dict(result='PASS',records=records,scope='Lossless diagnostic image compaction only; consumers should use recorded PNG after verifying its hash.')
Path(str(prefix)+'-image-compaction.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(result='PASS',images=len(records),source_bytes=sum(r['source_bytes'] for r in records))))
