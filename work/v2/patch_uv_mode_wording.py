from pathlib import Path
p=Path(r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port\work\v2\make_seamless_texture.py')
s=p.read_text()
s=s.replace('''"""Upscale a captured texture and blend RGB borders for GL_REPEAT.

Experimental single-asset tool only; output is not a complete/release pack.
Optional generated detail supplies RGB; captured source alpha is preserved.
"""''','''"""Upscale a captured texture, optionally blending borders for GL_REPEAT.

Experimental single-asset tool only; output is not a complete/release pack.
Optional generated detail supplies RGB; source alpha is preserved. Use
--uv-atlas for non-repeating atlases so opposite borders remain independent.
"""''')
s=s.replace('''    if isinstance(seamless, bool) is False:
        raise ValueError("seamless must be a boolean")''','''    if not isinstance(seamless, bool):
        raise ValueError("seamless must be a boolean")''')
p.write_text(s)
print('updated docstring and boolean validation')
