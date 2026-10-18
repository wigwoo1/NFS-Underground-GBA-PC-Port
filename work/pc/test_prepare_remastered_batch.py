import json
from pathlib import Path
import tempfile
from PIL import Image
import prepare_remastered_batch as p

workspace = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='supir-source-test-', dir=workspace) as tmp:
    root = Path(tmp).resolve()
    assert root.parent == workspace and root.name.startswith('supir-source-test-')
    source = root / 'source-export'
    (source / 'source').mkdir(parents=True)
    rgba = bytes([1, 2, 3, 0, 4, 5, 6, 127])
    key = p.source_id(rgba, 2, 1)
    data = p.png_bytes(Image.frombytes('RGBA', (2, 1), rgba))
    image = source / 'source' / (key + '.png')
    image.write_bytes(data)
    entry = dict(source_hash=key, png_sha256=p.digest(data), rgba_sha256=p.digest(rgba),
                 width=2, height=1, model=False, wall=True, uses=[])
    (source / 'inventory.json').write_text(json.dumps(dict(
        result='VERIFIED_EXACT_NATIVE_RGBA_SOURCE_EXPORT', sources=[entry],
        source_count=1, excluded_indexed_variants=[])))
    output = root / 'batch'
    result = p.prepare(source, output)
    job = result['jobs'][0]
    assert job['has_transparency']
    assert (job['target_width'], job['target_height']) == (4096, 2048)
    before = (output / 'batch.json').read_bytes()
    try:
        p.prepare(source, output)
        raise AssertionError('Existing batch accepted')
    except ValueError:
        pass
    assert (output / 'batch.json').read_bytes() == before
    image.write_bytes(data + b'changed')
    try:
        p.prepare(source, root / 'invalid')
        raise AssertionError('Changed source accepted')
    except ValueError:
        pass
    assert not (root / 'invalid').exists()
print('PASS: transparent RGB/alpha roundtrip; exact-aspect 4K target; existing batch preserved; changed input rejected before output')
