import sys
from pathlib import Path
path=Path('work/camera/test_prepared_pair_4k_candidate.py');source=path.read_text()
marker='import owned_d3d_call_profile_install_candidate\n'
source=source.replace(marker,marker+'''from owned_uncovered_window_candidate import OwnedD3DConsumer
reference_render=OwnedD3DConsumer.render
import owned_ordered_render_tail_install_candidate
candidate_render=OwnedD3DConsumer.render
''')
source=source.replace("expected=[dict(alpha=0.001)]+expected+[dict(alpha=0.999)]","expected=[dict(alpha=0.5,variant=v,pair=p) for p in range(40) for v in (('reference','candidate') if p%2==0 else ('candidate','reference'))]")
source=source.replace("  alpha=item['alpha'];", "  OwnedD3DConsumer.render=reference_render if item['variant']=='reference' else candidate_render\n  alpha=item['alpha'];")
source=source.replace("rows.append(dict(alpha=alpha,sha256=row['native_rgb_sha256']))","rows.append(dict(alpha=alpha,variant=item['variant'],pair=item['pair'],sha256=row['native_rgb_sha256'],stages=row['consumer_stages']))")
source=source.replace("tuple(x['alpha'] for x in expected)","(0.5,)")
source=source.replace('prepared-pair-4k-','ordered-tail-matched-')
exec(compile(source,str(path),'exec'),dict(__name__='__main__',__file__=str(path)))


