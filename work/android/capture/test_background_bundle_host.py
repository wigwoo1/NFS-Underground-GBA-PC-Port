"""Strict host validation of diagnostic NRB1 background/scene ownership."""
import json, struct
from pathlib import Path


def validate(data):
    def require(ok):
        if not ok: raise ValueError('Invalid background scene bundle')
    require(len(data) >= 128)
    h = struct.unpack_from('<16Q', data)
    require(h[:3] == (0x3142524e, 1, len(data)))
    require((h[5], h[7]) in ((1, 1), (2, 2)))
    require(h[6] == 0 if h[5] == 1 else 0 < h[6] < 160)
    require(h[14:] == (0, 0))
    cursor = 128
    parts = []
    for i in range(3):
        off, size = h[8+i*2:10+i*2]
        if i == 2 and h[7] == 1:
            require((off, size) == (0, 0)); continue
        require(off == cursor and size > 0 and size <= len(data)-off)
        parts.append(data[off:off+size]); cursor += size
    require(cursor == len(data))
    sky = parts[0]
    require(len(sky) >= 128)
    sh = struct.unpack_from('<16Q', sky)
    require(sh[:3] == (0x3142534e, 1, len(sky)) and sh[3:8] == h[3:8])
    require(sh[8] == 128 and 128 <= sh[9] <= len(sky)-128)
    nab = sky[128:128+sh[9]]
    require(len(nab) >= 128)
    nh = struct.unpack_from('<16Q', nab)
    require(nh[:3] == (0x3142414e, 1, len(nab)) and nh[3:8] == h[3:8])
    coverage = []
    for i, bg in enumerate(parts[1:]):
        require(len(bg) == 76880)
        b = struct.unpack_from('<10Q', bg)
        require(b[:3] == (0x3147424e, 1, len(bg)))
        off, size = nh[8+i*2:10+i*2]
        require(off >= 128 and size >= 32 and off+size <= len(nab))
        serial, begin, end, page = struct.unpack_from('<4I', nab, off+16)
        require(b[3:] == (h[3], serial, begin, end, end+1, page, 38400))
        mask = bg[38480:]
        require(all(v in (0, 1) for v in mask) and any(mask))
        so, sn = sh[10+i*2:12+i*2]
        require(sn == 30568 and so >= 128 and so+sn <= len(sky))
        require(bg[80+10560:80+25696] == sky[so+56:so+15192])
        require(all(mask[10560:25696]))
        coverage.append(sum(mask))
    return coverage


def main():
    folder = Path(r'C:\NFSUG-Workspace\NFSUG-android-source-background-local')
    results = {}; rejected = 0
    for name in ('whole', 'split'):
        data = (folder/f'race-background-{name}.nrb').read_bytes()
        results[name] = validate(data)
        h = struct.unpack_from('<16Q', data)
        mutations = [(0, 0), (8, 2), (16, len(data)+1), (24, h[3]+1),
                     (32, h[4]+1), (56, 3), (64, 129), (112, 1),
                     (h[10]+24, h[3]+1), (h[10]+32, 999),
                     (h[10]+56, 0), (h[10]+64, 2)]
        for offset, value in mutations:
            bad = bytearray(data); struct.pack_into('<Q', bad, offset, value)
            try: validate(bad)
            except ValueError: rejected += 1
            else: raise AssertionError(f'Accepted mutation {name} at {offset}')
        for bad in (data[:-1], data+b'\0'):
            try: validate(bad)
            except ValueError: rejected += 1
            else: raise AssertionError('Accepted wrong length')
    report = dict(result='PASS_BACKGROUND_BUNDLE_VALIDATION', coverage=results,
                  malformed_rejected=rejected, diagnostic_only=True)
    (folder/'background-bundle-validation-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))

if __name__ == '__main__': main()
