"""Expand original artwork inventory from one verified frozen traffic snapshot."""
from pathlib import Path
import hashlib, io, json, shutil, struct, subprocess
from PIL import Image
from prepare_remastered_batch import source_id

local = Path(__file__).resolve().parent
root = Path('Y:/CODEX/NFSUG-Native-PC-Port')
base = Path('C:/NFSUG-Workspace')
fixture = base / 'NFSUG-Android-Traffic-20261017/gap3519-results'
dest = root / 'outputs/nfsug-native-renderer/texture-sources/native-with-traffic-20261017'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
receipt_path = fixture / 'first-gap-report.json'
receipt = json.loads(receipt_path.read_text())
assert receipt['result'] == 'VERIFIED_ANDROID_FIRST_GAP_COMPONENT_WITNESS'
assert receipt['step3519']['retained_retry_present']
for name, digest in receipt['frozen_component_sha256'].items():
    assert sha(fixture / name) == digest, name
gpu_path = base / 'NFSUG-Android-Traffic-20261017/traffic-gpu-results/traffic-scene-gpu-report.json'
gpu = json.loads(gpu_path.read_text())
assert gpu['result'] == 'PASS_TRAFFIC_SCENE3519_RETAINED_GPU'
assert gpu['scene']['epoch'] == 2 and gpu['scene']['refresh'] == 15360
assert gpu['scene']['commands'] == 17
dest.mkdir(parents=True, exist_ok=True)
raw_path = dest / 'traffic15360.textures'
assert not raw_path.exists(), 'Do not overwrite a previous export'
command = [str(base / 'android-tools/jdk-21.0.12.1+1/bin/java.exe'), '-Xmx512m',
           '-cp', str(local / 'traffic-texture-classes'),
           'org.codex.nfsugpreview.PcTrafficTextureExport', str(fixture), str(raw_path)]
run = subprocess.run(command, check=True, capture_output=True, text=True, timeout=90)
assert 'PASS_FROZEN_TRAFFIC_TEXTURE_EXPORT' in run.stdout
assert raw_path.stat().st_size < 64*1024*1024
(dest / 'java-export.log').write_text(run.stdout + run.stderr, encoding='utf-8')
prior = root / 'outputs/nfsug-native-renderer/texture-sources/current-native-sample-20261017'
inventory = json.loads((prior / 'inventory.json').read_text(encoding='utf-8'))
entries = {row['source_hash']: dict(row) for row in inventory['sources']}
(dest / 'source').mkdir(exist_ok=True)
for identity, row in entries.items():
    original = prior / 'source' / (identity + '.png')
    assert sha(original) == row['png_sha256']
    shutil.copyfile(original, dest / row['source'])
stream = io.BytesIO(raw_path.read_bytes())
def read(n):
    value = stream.read(n)
    assert len(value) == n
    return value
def integer():
    return struct.unpack('>I', read(4))[0]
assert integer() == 0x4e545831
epoch, refresh, owners, commands = struct.unpack('>2Q2I', read(24))
assert (epoch, refresh, owners, commands) == (2, 15360, 1, 17)
original_count = len(entries)
indexed = {}
occurrences = 0
for _ in range(commands):
    owner, index, material, width, height = struct.unpack('>5I', read(20))
    model, is_indexed, wall, lit = struct.unpack('>4?', read(4))
    levels = integer()
    assert levels == (16 if lit else 1)
    for level in range(levels):
        size = integer()
        assert 0 < width <= 4096 and 0 < height <= 4096 and size == width*height*4
        rgba = read(size)
        identity = source_id(rgba, width, height)
        digest = hashlib.sha256(rgba).hexdigest()
        use = dict(scene='traffic15360.textures', epoch=epoch, refresh=refresh, owner=owner,
                   command=index, material_index=material, lighting_level=level, lit=lit)
        if is_indexed:
            indexed.setdefault(identity, dict(width=width, height=height, source_key=identity,
                upload_rgba_sha256=digest, indexed=True, model=model, wall=wall, uses=[]))['uses'].append(use)
            continue
        occurrences += 1
        if identity not in entries:
            png = dest / 'source' / (identity + '.png')
            Image.frombytes('RGBA', (width, height), rgba).save(png)
            entries[identity] = dict(source='source/'+png.name, width=width, height=height,
                source_hash=identity, rgba_sha256=digest, png_sha256=sha(png), model=model, wall=wall, uses=[])
        row = entries[identity]
        assert (row['width'], row['height'], row['rgba_sha256']) == (width, height, digest)
        with Image.open(dest / row['source']) as image:
            assert image.size == (width, height) and image.convert('RGBA').tobytes() == rgba
        row['uses'].append(use)
assert not stream.read()
assert len(list((dest / 'source').glob('*.png'))) == len(entries)
excluded = {row['source_key']: row for row in inventory['excluded_indexed_variants']}
for identity, row in indexed.items():
    if identity in excluded:
        assert excluded[identity]['upload_rgba_sha256'] == row['upload_rgba_sha256']
    else:
        excluded[identity] = row
inventory.update(source_count=len(entries), source_png_bytes=sum((dest/r['source']).stat().st_size for r in entries.values()),
    sources=list(entries.values()), additional_scene=dict(name=raw_path.name, sha256=sha(raw_path),
    epoch=epoch, refresh=refresh, owners=owners, commands=commands),
    additional_indexed_variants=list(indexed.values()), excluded_indexed_variants=list(excluded.values()),
    limits='Ten frozen scenes including repaired traffic endpoint. Exact decoded upload sources only; no full-game coverage, enhancement or live integration. Indexed texture variants remain metadata only.')
inventory.pop('runner_sha256', None)
inventory['runner_sha256'] = sha(Path(__file__))
(dest / 'inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
java_sources = {}
for path in (local / 'traffic-texture-classes').rglob('*.class'):
    name = path.name.split('$')[0].split('.')[0] + '.java'
    source = local/name if name == 'PcTrafficTextureExport.java' else root/'work/android/java/org/codex/nfsugpreview'/name
    java_sources[str(source)] = sha(source)
report = dict(result='VERIFIED_FROZEN_TRAFFIC_TEXTURE_COVERAGE', original_sources=original_count,
    combined_sources=len(entries), added_true_color_sources=len(entries)-original_count,
    traffic_true_color_occurrences=occurrences, traffic_indexed_variants=len(indexed),
    frozen_inputs=receipt['frozen_component_sha256'], witness_receipt_sha256=sha(receipt_path),
    gpu_receipt_sha256=sha(gpu_path), textures_sha256=sha(raw_path),
    compiled_java_source_sha256=java_sources, exporter_sha256=sha(local/'PcTrafficTextureExport.java'),
    inventory_sha256=sha(dest/'inventory.json'), complete=False, regenerated=False, renderer_changed=False)
(dest / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
for name in ('PcTrafficTextureExport.java', 'export_traffic_texture_sources.py'):
    shutil.copyfile(local/name, root/'work/pc'/name)
    assert (local/name).read_bytes() == (root/'work/pc'/name).read_bytes()
assert not (dest/'pack.ready').exists()
print(json.dumps({k:v for k,v in report.items() if k not in ['frozen_inputs','compiled_java_source_sha256']}, indent=2))
