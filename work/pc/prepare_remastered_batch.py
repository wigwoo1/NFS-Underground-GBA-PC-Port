"""Prepare traceable SUPIR inputs, not restored artwork or a release pack."""
import argparse
import hashlib
import io
import json
from pathlib import Path
from PIL import Image


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_id(rgba, width, height):
    data = width.to_bytes(4, 'little') + height.to_bytes(4, 'little') + rgba
    value = 0xcbf29ce484222325
    for byte in data:
        value = ((value ^ byte) * 0x100000001b3) & 0xffffffffffffffff
    return f'{value:016x}'


def png_bytes(image):
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue()


def prepare(source, output):
    inventory_bytes = (source / 'inventory.json').read_bytes()
    inventory = json.loads(inventory_bytes)
    if inventory['result'] != 'VERIFIED_EXACT_NATIVE_RGBA_SOURCE_EXPORT':
        raise ValueError('Expected a verified original source export')
    pending = []
    identities = set()
    for entry in inventory['sources']:
        identity = entry['source_hash']
        if len(identity) != 16 or any(c not in '0123456789abcdef' for c in identity) or identity in identities:
            raise ValueError('Invalid or duplicate source identity')
        identities.add(identity)
        # Use canonical filenames; never trust an inventory path outside source/.
        original = (source / 'source' / (identity + '.png')).read_bytes()
        if digest(original) != entry['png_sha256']:
            raise ValueError('Original PNG changed: ' + identity)
        with Image.open(io.BytesIO(original)) as image:
            rgba = image.convert('RGBA')
        width, height = rgba.size
        raw = rgba.tobytes()
        if ((width, height) != (entry['width'], entry['height']) or
                digest(raw) != entry['rgba_sha256'] or source_id(raw, width, height) != identity):
            raise ValueError('Original pixel identity changed: ' + identity)
        longest = max(width, height)
        if longest > 4096 or 4096 % longest:
            raise ValueError('Needs explicit aspect-preserving target review: ' + identity)
        scale = 4096 // longest
        rgb = rgba.convert('RGB')
        alpha = rgba.getchannel('A')
        # Lossless channel separation only; no enhancement or enlargement here.
        rgb_data, alpha_data = png_bytes(rgb), png_bytes(alpha)
        assert Image.open(io.BytesIO(rgb_data)).tobytes() == rgb.tobytes()
        assert Image.open(io.BytesIO(alpha_data)).tobytes() == alpha.tobytes()
        assert Image.merge('RGBA', (*rgb.split(), alpha)).tobytes() == raw
        job = dict(source_hash=identity, original_rgba_sha256=entry['rgba_sha256'],
                   original_png_sha256=entry['png_sha256'], width=width, height=height,
                   target_width=width*scale, target_height=height*scale, upscale=scale,
                   input_rgb='rgb/' + identity + '.png', input_rgb_sha256=digest(rgb_data),
                   original_alpha='alpha/' + identity + '.png', original_alpha_sha256=digest(alpha_data),
                   has_transparency=alpha.getextrema() != (255, 255),
                   review_required=True, supir_output=None,
                   material_flags=dict(model=entry['model'], wall=entry['wall']),
                   source_uses=entry['uses'])
        pending.append((job, rgb_data, alpha_data))
    if len(pending) != inventory['source_count']:
        raise ValueError('Source count mismatch')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output must be empty; preserve any earlier artwork')
    for folder in ('rgb', 'alpha'):
        (output / folder).mkdir(parents=True, exist_ok=True)
    for job, rgb_data, alpha_data in pending:
        (output / job['input_rgb']).write_bytes(rgb_data)
        (output / job['original_alpha']).write_bytes(alpha_data)
    manifest = dict(format='NFSUG-SUPIR-INPUT-BATCH-1', mode='Remastered',
                    result='VERIFIED_LOSSLESS_SUPIR_INPUT_PREPARATION',
                    inventory_sha256=digest(inventory_bytes), complete=False,
                    sample_only=True, supir_executed=False, ready_marker_created=False,
                    source_count=len(pending), indexed_variant_count=len(inventory['excluded_indexed_variants']),
                    target_policy='4096-pixel longest edge; exact source aspect ratio',
                    alpha_policy='Original alpha stored losslessly. SUPIR RGB output must be recombined with reviewed scaled alpha; no final alpha or pack produced.',
                    upstream='https://github.com/Fanghua-Yu/SUPIR',
                    limits='Sampled frozen scenes only; lighting/alpha are baked into these source identities. Not complete-game coverage. Review texture seams, UVs, colors, logos/text, fine material detail and palette behavior before runtime integration.',
                    jobs=[row[0] for row in pending])
    path = output / 'batch.json'
    path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    saved = json.loads(path.read_text(encoding='utf-8'))
    for job in saved['jobs']:
        for filename, checksum in [('input_rgb', 'input_rgb_sha256'), ('original_alpha', 'original_alpha_sha256')]:
            assert digest((output / job[filename]).read_bytes()) == job[checksum]
    assert not (output / 'pack.ready').exists()
    return saved


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = prepare(args.source, args.output)
    print(json.dumps({key: value for key, value in manifest.items() if key != 'jobs'}, indent=2))
