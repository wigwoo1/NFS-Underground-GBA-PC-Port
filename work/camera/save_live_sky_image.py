from pathlib import Path
p=Path('work/camera/live_source_sky_pixels_candidate.py');s=p.read_text();s=s.replace("pixels=buffer.raw;crop=", "pixels=buffer.raw\n      if not self.sky_pixel_diagnostics:\n       from PIL import Image\n       Image.frombytes('RGB',(3840,2160),pixels).save('work/camera/live-sky-selected-first.png')\n      crop=")
p.write_text(s)
