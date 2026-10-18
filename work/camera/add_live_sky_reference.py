from pathlib import Path
p=Path('work/camera/live_source_sky_pixels_candidate.py');s=p.read_text();needle="      self.sky_pixel_diagnostics.append(dict(metadata[position]"
assert s.count(needle)==1
addition='''      from owned_sky_color import sky_rgba
      sampled_frame=rows[position][5][0];gn,hn=struct.unpack_from('<2I',sampled_frame,8)
      assert hn==160*34944
      palettes=b''.join(sampled_frame[40+gn+y*34944+32896:40+gn+y*34944+32896+512] for y in range(160))
      reference=sky_rgba(rows[position][-1],palettes);points=[]
      for sy in range(44,59,2):
       for sx in range(8,232,12):
        pixel=(int((sy+.5)*13.5)*3840+int(300+(sx+.5)*13.5))*3
        ref=((sy-44)*240+sx)*4
        actual=list(pixels[pixel:pixel+3]);expected=list(reference[ref:ref+3])
        points.append(dict(x=sx,y=sy,actual=actual,expected=expected,matches=max(abs(a-b) for a,b in zip(actual,expected))<=1))
'''
s=s.replace(needle,addition+needle).replace('crop=[300,600,3540,800]))','crop=[300,600,3540,800],sky_reference_points=points))');p.write_text(s)
