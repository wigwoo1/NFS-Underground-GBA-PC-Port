"""Conservative diagnostic root-block anchors; never infers within-block order."""
def root_anchors(sampled_regions, records, pass_index=0):
    if pass_index not in (0,1) or len(set(sampled_regions))!=len(sampled_regions):
        raise ValueError('ambiguous sampled root occurrences')
    caller=(0x03004da4,0x03004de8)[pass_index]
    roots=[r for r in records if r[4]==caller and r[8]==0 and r[5]==pass_index]
    regions=[r[0]&65535 for r in roots]
    if not roots or len(set(regions))!=len(regions):raise ValueError('ambiguous captured roots')
    if any(r[6]>r[7] for r in roots) or any(a[7]>b[6] for a,b in zip(roots,roots[1:])):raise ValueError('invalid root command intervals')
    # Existing calls must remain a subsequence: omissions/reordering need a richer planner.
    if [r for r in sampled_regions if r in regions]!=regions:raise ValueError('captured root removed or reordered')
    starts=dict(zip(regions,[r[6] for r in roots]));result={}
    for i,region in enumerate(sampled_regions):
        if region in starts:result[region]=starts[region];continue
        following=next((r for r in sampled_regions[i+1:] if r in starts),None)
        if following is None:raise ValueError('no following captured root anchor')
        result[region]=starts[following]
    return result
