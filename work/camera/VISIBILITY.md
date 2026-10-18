# Original visibility queue: evidence and next boundary

The world state at `030000C0` contains a queue pointer at `+60` and a retained
entry count at `+EE`. Observed records are 16 bytes, interpreted as eight
little-endian halfwords:

| Offset | Observed use |
| --- | --- |
| 0 | Geometry descriptor index, stride 48 from state `+14` |
| 2, 4 | Left and right viewport bounds |
| 6, 8 | Top and bottom viewport bounds |
| A | Flags; consumer tests bits 8 and 80 |
| C | Traversal field; builder tests value at most 4 |
| E | Not yet recovered |

Original ARM `03002898..030028C0` copies these four bounds into the world state
at `+E2..+E8` immediately before geometry transform/draw. `03002960` calls the
observed world entry at `03001800`. `03002C18..03002C44` performs the same copy
in another geometry traversal path. This is a group-level visibility queue,
not a per-wall material property.

`03004C74` initializes traversal and builds the queue. It starts with a count
of one, walks 16-byte records, calls `03002B74`, optionally calls `0300556C`,
and stores the resulting halfword count at state `+EE`. Its loop checks count
against 20; do not assume malformed or overflow behavior is safe. `03005620`
is called afterward and its effect remains to be recovered.

`03004D5C` consumes the queue in reverse order, calling `030027F0` when flag 8
is clear. A second reverse pass calls the same routine with mode 1 when both
flags 8 and 80 are clear. `030027F0` can recurse through descriptor links;
object drawing via `0300220C` can also call it with a temporary stack record.
Do not assume every drawn surface has a unique retained queue record.

Reproducible evidence:

- `capture_visibility.py` loads the existing driving state with saving disabled,
  reads only after original stepping returns, and captures queue data at scene
  serials 0, 40 and 200. All three scene packets match the retained references
  byte-for-byte. Their queues contain 11, 5 and 7 entries respectively.
- `audit_visibility_queue.py` matches source ranges plus all four bounds for
  21 of 22 scene-0 walls. Arrow wall `0857C6F4` has no direct queue source-range
  match. Its observed world descriptor is `0856AD00`; its world-entry r6 is
  a stack pointer (`03007DC8`). An object/recursive temporary entry is a
  candidate explanation, not yet independently established for this draw.
- The arrow bounds `[54,98,0,158]` remain known from the wall capture, but
  absence of a direct queue entry is not grounds to omit it from snapshots.

Next: isolate queue builder `03004C74` with captured full state, track writes
and linked descriptor traversal, and recover the temporary object draw path.
Then recompute visibility for the interpolated rigid camera pose. Captured
screen bounds are diagnostic evidence only and must not be frozen or matched
between frames to produce motion. Current packets retain world geometry but
not this queue or the full linked visibility structure.

## Isolated replay follow-up

`replay_visibility.py` now executes the queue builder with full EWRAM/IWRAM
captured after stepping returns. Scene 0 and 40 queues reproduce byte-for-byte.
Scene 200 does not: replay yields six entries versus seven retained, with 30
different bytes including the length difference. Post-step state may differ
from builder-entry state, or additional initialization may be required; neither
explanation is yet proved. The report explicitly labels this result PARTIAL.

The scene-0 reverse traversal reproduces all 22 wall sources and bounds in
captured order, with original wall setup executing and terminal pixel routines
bypassed. The arrow originates from object `0200545C`. At `03002360`, original
code calls `030027F0` with the temporary record
`[181,54,98,0,158,0,0,65535]`; its return address is `03002364`. The later arrow
wall call uses these same bounds. This establishes the temporary object path
for that missing direct-queue match. Stack addresses in the isolated replay
differ from the live trace because the harness uses its own stack.

Next boundary: obtain or reconstruct builder-entry initialization for scene
200 and audit object-linked records beyond this one captured view. Native
queue construction and visibility at intermediate camera poses remain absent.

## Camera coherence investigation

The scene-200 packet camera position is `(-6465,-100,2523)`, but the post-step
memory camera position is `(-6286,-100,2553)`. The matching raw matrix was last
observed after step 791, while the completed packet was delivered at step 792.
Scenes 0 and 40 have no such mismatch. Capture now retains sixteen recent
camera/projection samples, requiring matching-position matrices to be unique
before selecting one for the diagnostic.

Restoring only scene 200's render camera in the isolated replay recovers seven
entries but leaves four differing bound bytes: offsets 18/20/34/36 are
0/92/92/230 versus expected 2/89/89/238. Restoring its projection as well does
not establish equality. Testing all sixteen recent camera/projection pairs
against the completed memory snapshot yields no exact scene-200 queue. Six
full memory snapshots after steps 786..791 also fail to reproduce that queue.
Thus camera advancement is real and explains part of the discrepancy, but is
not a complete explanation. The result remains PARTIAL; exact builder-entry
capture is the next dependency, rather than further guessing at field values.

All camera replacements occur only in isolated Unicorn memory. The emulator,
ROM, saved driving state and ordinary renderer are unmodified.

## Exact builder-entry capture

The separate `visibility-probe.dll` enables `NF_VISIBILITY_CAPTURE`; ordinary
builds omit the hook. `nf_visibility_capture(path, ordinal)` writes one bounded
entry/exit pair at `03004C74` and `03004D50`, including registers, native scene
serial, and EWRAM/IWRAM. Status 2 means complete, 3 means capture failure.
`build-visibility-probe.ps1` links the existing mGBA archive without replacing
the ordinary bridge DLL or synchronized fallback.

`test_visibility_entry.py` captures builder ordinal 200 at frame 9630, native
scene serial 200. Replaying its exact input reproduces all seven output queue
entries byte-for-byte. Across 850 original simulation steps, diagnostic and
baseline runs produce identical hashes for all 214 scene packets and identical
final EWRAM/IWRAM/VRAM. This validates the entry/exit oracle and non-invasive
capture, not native visibility translation.

The actual builder output itself differs from the later scene-200 queue in
the same four bound bytes. Isolated reverse traversal from builder output
does not write the queue or resolve those differences. Thus the earlier
comparison used a later-stage queue as the builder oracle; exact builder
replay is now verified, but subsequent queue evolution remains unresolved.
Next: trace original queue writes between builder exit and the later capture
to identify the additional processing, without assuming the reverse draw
consumer performs it. Native snapshots must retain the appropriate stage.

## Queue mismatch resolved: next-scene reuse

The diagnostic build now records bounded byte/halfword/word stores to the
captured queue for four subsequent refreshes. The four differing bounds are
written at frame 9633 with **native scene serial 201**, after scene 200 closes:

| Queue byte offset | ARM writer | New halfword |
| --- | --- | --- |
| 18 | 03002E78 | 2 |
| 20 | 03002ECC | 89 |
| 34 | 03002E94 | 89 |
| 36 | 03002EC0 | 238 |

Applying all 22 observed stores through delivery frame 9633 to scene 200's
builder output reproduces the post-step queue byte-for-byte. All those stores
belong to serial 201. The later memory snapshot is therefore already a shared
queue being rewritten for the next scene, not an alternate result of scene
200's builder or reverse draw consumer. Earlier PARTIAL replay reports remain
historical evidence of comparing different stages/scenes; this cause is now
resolved by exact-entry capture and a verified write sequence.

With the write recorder enabled, all 214 packet hashes and final three RAM
regions still match the ordinary bridge after 850 steps. Store-multiple writes
are not instrumented; completeness is established for this observed sequence
by exact byte reconstruction, not claimed for arbitrary future captures.

Next: translate queue construction against exact entry/output pairs. Any
visibility data added to live scene packets must be copied while its scene
owns the shared queue; reading it after nf_frame returns is insufficient.

## First native queue stage

`native_visibility.c` translates original `03005620` as
`nfs_visibility_merge`. The state `+64` table contains 8-byte groups indexed
by descriptor: one count byte followed by up to seven queue indices. For each
unhidden queue entry, a group with multiple members combines their signed
horizontal minimum/maximum into the first member and marks later members
with flag 8. Other record fields remain unchanged. Processing order and
already-marked entries follow the original code.

The API bounds queues to 20 entries and descriptor groups to 512. Malformed
referenced indices/counts fail before publishing any changes, using a private
320-byte work buffer. It does not implement geometry traversal, projection,
object recursion or a full visibility builder.

`test_visibility_merge.py` passes 600 deterministic original-ARM comparisons,
546 of which change queue bytes. Cases include signed bounds, flags, duplicate
indices and empty queues. A malformed group after an earlier valid merge
preserves the entire caller queue. In a fresh Unicorn instance, the native
function replaces exactly one original `03005620` call while the captured
scene-200 builder executes; its seven-entry output remains byte-identical to
the actual captured builder output. An explicit replacement-count assertion
prevents an unexecuted hook from being reported as successful integration.

Next: native queue append/link processing (`0300556C`) and world-edge traversal
(`03002B74`), retaining the original builder oracle for differential checks.

## Native linked-record append

`nfs_visibility_append` translates `0300556C`. Descriptor offset `+20` selects
the linked descriptor, with `FFFF` meaning no link. A new record copies the
source vertical bounds and traversal field, obtains horizontal bounds from
the current viewport, uses flag `80`, and stores the source descriptor at
record `+E`. It advances the destination index and both counters. Queue
capacity is checked before changing bytes/counters; absent links are a no-op
even when the queue is full.

`test_visibility_append.py` passes 600 original-ARM comparisons: 480 positive
links and 120 absent links, including counter wrapping and arbitrary halfword
bounds. It compares all queue bytes and the destination/total/link counters.
Full-queue rejection preserves bytes and counters. The combined builder test
now replaces seven append calls and one merge call, retaining exact seven-entry
output. All seven append calls in this captured scene are absent links; positive
append behavior is covered by the separate original-ARM tests, not claimed as
positive-link coverage from this particular real scene.

Next: translate the world-edge traversal/queue insertion at `03002B74`, and
capture a builder case containing a positive linked append for broader composed
coverage. Native routines remain isolated components, not live rendering.

## Native projected-edge gate and record

`nfs_visibility_edge_record` translates `03002E18..03002F14`, after world
transform, near clipping and projection. It rejects reversed/outside candidates,
combines projected bounds with the parent record, preserves the original
near-clipped endpoint rules (left 2, right 238), sets descriptor/vertical bounds,
increments traversal depth and derives flags from parent/material and endpoint
depth. Record offset E is deliberately preserved because this block does not
write it. Return values distinguish invalid inputs, culled edges and accepted
records; invalid/culled candidates leave the destination unchanged.

`test_visibility_edge.py` passes 1,200 original-ARM block comparisons: 476
accepted and 724 culled, including signed endpoints, near-clip flags and depth
threshold cases. The combined captured-builder test now substitutes 14 native
edge calls (six accepted), seven absent-link append calls and one merge call.
Its seven-entry result remains byte-identical to the actual original output.
Existing 600 merge and 600 append comparisons also pass.

This translates original reference visibility arithmetic, not projected-polygon
motion matching. Camera-space transform, near clipping, projection, membership
insertion and orchestration remain original ARM in the composed test. Next:
native membership insertion and world-edge transform/projection, then evaluate
the recovered visibility logic using intermediate rigid camera poses.

## Native membership insertion

`nfs_visibility_insert` translates `03002F14..03002F60` for representable groups.
It appends the current queue index to the descriptor's seven-slot membership
group and advances the destination index and total counter. Full queues,
out-of-range descriptors and an eighth member fail before changing outputs.
This intentionally rejects the original routine's overflowing count behavior;
the later native merge stage cannot safely consume such a count.

`test_visibility_insert.py` passes 700 original-ARM cases spanning all valid
prior membership counts 0..6, queue indices 0..19 and unsigned counter wrap.
Four invalid/full cases preserve the table and counters. The composed builder
test replaces six insertions along with 14 candidate gates, seven absent-link
appends and one merge. Both the seven-entry queue and all 4,096 membership-table
bytes match the actual capture. The 600 merge, 600 append and 1,200 candidate
comparisons also continue to pass.

Remaining native builder work: camera-space transform, near clipping,
projection and orchestration. The four translated stages remain test-harness
substitutions; they are not enabled in the live renderer.

## Native camera-space clipping and projection

`nfs_visibility_project` translates `03002D20..03002E18`. It distinguishes
both-behind-near rejection from the original far-depth traversal stop at
depth greater than `6000` hex. A crossing endpoint uses original reciprocal
lookup and signed multiply with ARM 32-bit wrapping; projected bounds retain
the original integer shifts and optional endpoint ordering. It returns the
clipped depths and endpoint flags required by the native candidate-record
stage. Invalid reciprocal indices fail without publishing output.

`test_visibility_project.py` passes 1,805 original-ARM comparisons: 1,732
projected, 37 near rejections and 36 far stops. Projected cases include 210
left-endpoint clips, 224 right-endpoint clips and 1,298 unclipped edges.
The composed builder executes 15 native projection calls, 14 reaching the
native candidate gate. All later native stages preserve both captured queue
and membership-table bytes; existing component regressions also pass.

This is an original-behavior visibility oracle, not low-resolution polygon
interpolation or a replacement for continuous high-resolution world geometry.
World-to-camera transformation and builder orchestration remain original ARM
in the composed harness. Those are the next translation boundary, followed by
testing visibility with intermediate rigid camera poses.

## Native world-to-camera edge transform

`nfs_visibility_transform` translates the planar transform in
`03002C80..03002D20`: add original camera translation, multiply X/Z by the
corresponding matrix terms, preserve 32-bit wrapping, then arithmetic-shift by
14. It processes two selected world endpoints; the caller selects the next
68-byte source record or closes the ring to its first record.

`test_visibility_transform.py` passes 900 original-ARM comparisons, including
300 closing-ring edges, normal-scale values and full-width arithmetic wrap.
The combined captured builder now uses native transform for all 15 tested
edges, including three closing edges. Native projection, record construction,
membership insertion, append and merge follow it; queue and full membership
table remain byte-identical. Projection and merge regression checks pass.

Remaining dependency: translate the original builder's traversal/orchestration
and provide coherent memory access through a bounded native snapshot. These
six routines currently execute only as substitutions in a diagnostic original-
ARM harness. They do not yet establish standalone native visibility, smooth
intermediate-pose visibility or live-renderer correctness.

## Complete native geometry-ring traversal

`nfs_visibility_traverse` replaces original `03002B74` for a single bounded
ring. Its caller supplies retained state, descriptor, source vertices, camera,
projection, parent record and reciprocal table. It composes transform,
clipping/projection, candidate construction and membership insertion, including
FFFF edge skips, ring closure, far-stop behavior and original viewport/state
side effects. A private state/queue/membership copy makes failures atomic.
Inputs are limited to 32 vertices, 20 queue entries and representable groups.

`test_visibility_traversal.py` compares all mutable outputs and the returned
total at each of seven actual original call boundaries, then separately
substitutes the entire native routine into the captured builder. Descriptors
17/19/18/21/290/16/20 have 4/5/5/10/3/6/7 edges and append 3/1/1/0/0/1/0 entries.
Both runs reproduce the final seven-entry queue and full membership table.
An overflow fixture also verifies that state, queue, table and counters remain
unchanged after a failed native traversal. The earlier stage-substitution
harness still passes.

Next: combine native traversal, linked append and merge under a standalone
outer queue loop with bounded snapshot reads. This ring routine is not yet
installed into live rendering, and intermediate camera poses remain untested.

## Standalone native queue builder

`nfs_visibility_build` now implements the outer `03004C74` queue loop using
native traversal, linked append and merge. It starts from the caller's already
initialized root record, resets membership data, follows the depth limit and
first-link behavior, and publishes the final count/state/queue/table together.
A bounded immutable snapshot callback serves descriptor, vertex, camera and
projection reads; checked address arithmetic prevents indexed-read wrapping.
The public buffer/reader contract is in `native_visibility.h`.

`test_visibility_builder.py` calls only the native DLL and immutable captured
data; it executes no ARM code. On exact scene-200 input, all 256 state bytes,
320 queue bytes (including unused records) and 4,096 membership bytes match
the captured original output. Injecting failure separately at each of its 17
snapshot reads leaves every output unchanged. Warnings-as-errors build and
whole-ring regression checks pass.

This is a standalone original visibility-builder component verified on one
real captured scene, not a complete renderer/engine. Broader coherent captures
(especially positive links), root initialization, object traversal, visibility
at intermediate rigid poses and live integration remain next dependencies.

## Broader standalone coverage

`audit_visibility_builder.py` captures bounded exact entry/exit pairs during
three 900-refresh runs from the driving state: straight, scripted left and
scripted right. All 69 samples (23 per run) match every state/queue/membership
byte with standalone native building. Capturing also preserves all scene packet
hashes and final EWRAM/IWRAM/VRAM against ordinary-bridge controls. Raw snapshots
remain private in `work/camera/visibility-corpus`.

No sampled record confirms a positive linked append. To cover composition of
that branch, `test_visibility_linked_builder.py` alters only a private in-memory
ROM copy, setting root descriptor 17's link to descriptor 21. Original ARM
execution confirms one positive append, and standalone native building matches
all state/queue/membership bytes with eight final entries. This is explicitly
a synthetic fixture, not evidence of that link in unmodified gameplay. The
supplied ROM file is only read.

Next: recover root-record initialization and integrate coherent snapshot data
for evaluating visibility between original poses; object draw traversal still
needs to be handled separately. Coverage is one scripted race, not every track
or a validation of displayed 60fps motion.

## Native root-record initialization

Original Thumb `08002F78..08002F90` copies viewport bounds into the root
record and clears flags/depth/parent. `08002FFA..08003010` sets the selected
descriptor and applies optional redirect at descriptor `+22`; `FFFF` means no
redirect. The original selected-descriptor global is `03005D44`. Selection
and fallback happen earlier and have not yet been translated.

`nfs_visibility_root` reconstructs the record from retained state viewport
`+58..+5E`, a supplied selected descriptor and its optional redirect. It reads
through the immutable snapshot callback and preserves output on invalid data
or read failure. `test_visibility_root.py` uses the coverage manifest (not
unfinished capture files), reconstructs all 69 root records byte-for-byte, then
uses those native records in the standalone builder. Every final state/queue/
membership buffer matches. Selected descriptors are 17,22,86,87,88; no redirects
occur in this corpus, so real-scene redirect coverage is not claimed.

The builder no longer needs a captured first queue record for these tests,
but still depends on captured region selection and viewport/camera state.
Next: spatial selection/fallback and coherent scene snapshot integration,
then object traversal and intermediate camera-pose tests.

## 2026-09-24 continuation: native world-region boundary primitive

Added nfs_visibility_contains for original ARM 03004BF4, the oriented half-plane test over 68-byte world records. It preserves 32-bit cross-product wrapping, accepts boundary points and reproduces empty-ring acceptance. The bounded API accepts up to 32 records and descriptor IDs below 512; invalid inputs leave the result unchanged. It is a region-boundary primitive, not complete spatial selection or a general polygon containment algorithm.

Added test_visibility_contains.py: all 1,024 original-ARM comparisons pass (87 accepted, 937 rejected), covering both ring orientations, boundary/exterior points, empty and single-point rings, ordinary coordinates and full-width arithmetic. Four invalid-input checks preserve output. Warnings-as-errors compilation passes; the existing 69 root-plus-complete-builder snapshot comparisons also pass.

Located original callers at 03000C28 and 03000CD8. The first uses state+EA as the descriptor, the second an edge's +32 descriptor. Thumb selection calls around 08002CD8/08002D32/08002D8C use trampoline 0806C098 with ROM literal difference 080726DC-08071E10 and dispatch base from global03006C50 plus E4. The surrounding Thumb path also calls fallback08022D78. These are concrete next tracing points; the enclosing selector and fallback remain untranslated and their state side effects need verification.

Archived source/header/test/report and updated VISIBILITY.md. Next dependency: recover complete spatial selector and fallback with coherent input snapshots, then intermediate-pose visibility and object/live renderer integration. This is component progress, not verified full-scene 60fps gameplay. ROM, saves, stable fallback and simulation timing remain unchanged.

## 2026-09-24 continuation: native local region selector

Added nfs_visibility_select, translating original ARM03000BD0..03000D44. It tests state+EA's current region against the world point at +C0/+C8, scans current-region edges in order if outside, resolves material flags through +2A or inline +2E, skips blocked/absent neighbors, tests neighbor rings and applies the +20 linked redirect when neighbor+8 is zero. All reads use an immutable snapshot callback with checked addresses and bounded geometry. No state mutation; errors preserve the output. The surrounding Thumb selector/fallback is not implemented.

Added test_visibility_select.py. All 133 original-ARM comparisons pass: 69 captured builder-entry states plus 64 explicitly synthetic two-region fixtures covering inside/outside/boundary positions, inline/material-backed restrictions, redirects and neighbor+8 gating. All 406 injected read failures preserve output. Warning-as-error DLL build passes; all 69 root-plus-builder regression comparisons also pass. These are function comparisons using builder-entry state, not captures of original selector-entry calls or proof that intermediate camera positions choose the correct complete scene.

The initial test harness incorrectly overwrote captured IWRAM with a ROM code image, corrupting the world state stored at030000C0 and causing an unmapped read. Fixed the harness to retain captured IWRAM exactly; only synthetic fixtures install the ROM code image and place their separate state in EWRAM. The full dataset then passed without excluding cases.

Archived source/header/test/report and updated VISIBILITY.md. Next dependency: exact selector-entry capture and enclosing Thumb fallback/selection composition, then coherent intermediate-pose visibility, complete object traversal and live rendering. This remains diagnostic native-component progress; full-scene 60fps gameplay and the complete port are not verified. ROM, saves, stable fallback and original timing are unchanged.

## 2026-09-24 continuation: native two-hop region fallback

Recovered Thumb08022D78..08022ECC and added nfs_visibility_fallback. The original fallback searches permitted edges of the current region, then permitted edges of each neighbor, testing containment only at second-hop destinations. Intermediate neighbors need not contain the query point. Both levels resolve material/inline blocking flags; destination +8/+20 control the linked redirect. Iteration preserves source order. Checked immutable reads, bounded rings and atomic output match the local selector API. Enclosing point construction and selection policy remain separate.

Added test_visibility_fallback.py. All 133 comparisons with original Thumb execution pass: 69 retained builder-entry states and 64 explicitly synthetic three-region-chain fixtures exercising restriction/redirect/inside/outside branches. Returned values include successful regions and FFFF no-match. All 1,608 individual snapshot-read failure injections preserve output. Original trampoline dispatch runs in the oracle (synthetic fixtures initialize its dispatch base); the native implementation executes no ARM/Thumb. Warnings-as-errors compilation passes, as do the existing 133 local-selector and 69 root-plus-builder comparisons.

These are component comparisons; retained captures are at builder entry, not the original selector entry. Next dependency: exact selection entry/exit snapshots and enclosing point construction/selection policy, then intermediate rigid-pose visibility and full scene/object live integration. No claim of verified full-scene 60fps gameplay or completed port. ROM, saves, stable synchronized fallback and original game timing remain unchanged. Archived source/header/test/report and updated VISIBILITY.md.

## 2026-09-24 continuation: exact local-selector capture verified

Extended the opt-in visibility capture bridge with nf_visibility_selector_capture. It records the actual local-selector entry03000BD0 and exit03000D44, retaining register headers and coherent EWRAM/IWRAM pairs. Selector capture disables the builder-specific subsequent queue-write watch. Existing builder capture API and ordinary bridge remain unchanged; only the diagnostic visibility-probe.dll was rebuilt.

Added test_selector_capture.py and a completed-capture manifest. During an 850-refresh run with scripted straight/left/right input, 24 actual selector-entry/exit pairs match native nfs_visibility_select return values exactly; both original and native preserve the 256-byte world state. A paired ordinary-bridge run produces the same 206 scene-packet hashes and identical final EWRAM/IWRAM/VRAM. Existing builder-entry capture regression also passes, including 214 matching scene packets, final memory equivalence and the previously explained next-scene queue writes.

Coverage limitation is explicit: these 24 sampled local calls return regions22/87, all retaining the input current region. They do not demonstrate an actual local neighbor transition or fallback invocation; those branches currently have synthetic component coverage. Raw snapshots remain private under work/camera/selector-corpus; compact reports, manifest, capture source and test are archived.

Next dependency: target actual transition/no-match calls and capture the enclosing point construction and selection/fallback policy, then coherent intermediate-pose visibility and full object/live renderer integration. No full-scene 60fps gameplay claim. ROM, saves, stable synchronized fallback and simulation timing are unchanged.

## 2026-09-24 continuation: real local-region transitions verified

Added nf_visibility_transition_capture to the opt-in diagnostic bridge. It retains a local-selector entry snapshot in RAM and publishes the entry/exit pair only when the returned region differs from the current region (including FFFF misses). Same-region calls discard their pending snapshot without writing it to disk. Pending memory is freed on cancellation, error and close; ordinary builder/selector capture modes remain available. Only the separate diagnostic DLL was rebuilt.

Added test_transition_capture.py with a completed-capture manifest. During the same 850-refresh scripted straight/left/right route, targeted capture records 24 actual local-region changes. Native selection matches every actual exit return; destinations are39,40,43,44,45,46,47,87,88. Original/native world state stays unchanged. Paired ordinary-bridge control yields identical 206 scene packets and final EWRAM/IWRAM/VRAM. The unfiltered selector regression (24 retained-region cases) and builder-entry regression (214 packets and memory equivalence) both still pass.

This closes the previous lack of actual local-neighbor transition evidence. None of these 24 targeted samples returned FFFF, so actual fallback invocation still lacks exact entry/exit capture. Raw pairs remain private in work/camera/transition-corpus. Archived capture source, test, compact report, manifest and updated VISIBILITY.md.

Next dependency: targeted no-match and Thumb fallback capture, then enclosing point/selection policy and coherent intermediate-pose visibility before full object/live renderer integration. These are exact engine-component checks, not proof of smooth full-scene 60fps gameplay. ROM, saves, stable synchronized fallback and simulation timing are unchanged.

## 2026-09-24 continuation: actual Thumb fallback captured

Added nf_visibility_fallback_capture to the diagnostic bridge, recording Thumb08022D78 entry and08022EDA exit through the existing instruction trace. work/probe.c invokes the capture event from thumbTrace only under NF_VISIBILITY_CAPTURE. The normal DLL and stable fallback remain unchanged. Existing capture modes still use their original boundaries.

Added test_fallback_capture.py. An initial 850-refresh route produced no fallback calls, so coverage was deliberately broadened to3,600 refreshes with repeated scripted turns. That run captured one actual fallback invocation; native nfs_visibility_fallback exactly matches its FFFF no-region result, and both original/native world state remain unchanged. All795 scene-packet hashes and final EWRAM/IWRAM/VRAM match a paired ordinary-bridge control. Completed captures are enumerated in a manifest; an empty pending file is not a completed sample. Raw snapshots remain private under work/camera/fallback-corpus.

Regression checks pass:24 actual local transitions with206 identical scene packets and memory, plus133 original-Thumb fallback component cases and1,608 read-failure injections. Successful fallback choices still have synthetic coverage only; the actual invocation captured here is a no-match. Source, test, compact report and manifest are archived alongside updated VISIBILITY.md.

Next dependency: enclosing selection policy/point construction (including what happens after both local and fallback no-match), then coherent intermediate rigid-pose visibility and object/live renderer integration. These checks do not establish full-scene60fps gameplay or a completed native port. ROM, saves, stable synchronized fallback and original simulation timing remain unchanged.

## 2026-09-24 continuation: composed paired-point selection policy

Recovered and implemented Thumb08002D06..08002D92 as nfs_visibility_pair. Inputs explicitly supply the selected region, fixed8 base X/Z and integer offset X/Z. The positive-offset point tries local selection, then two-hop fallback, then retains selected if both miss. The opposite-offset point runs local selection only and may returnFFFF. Final state reproduces the opposite point and selected-region fields. Signed fixed8 shift and wrapped addition/subtraction match the original. State and both results publish together only after all reads succeed.

Added test_visibility_pair.py. All276 original-Thumb sequence comparisons pass across69 retained world snapshots and four explicitly supplied offset fixtures per snapshot. Original execution includes132 fallback calls,128 retain-previous decisions and132 opposite-point misses; native results and all256 final state bytes agree. Sixty individually injected read failures leave state and both results unchanged. Warnings-as-errors build,69 root-plus-builder comparisons and133 fallback component comparisons with1,608 failure checks also pass.

This verifies composed control flow, including what happens when local and fallback both fail; the offset fixtures are synthetic variations, not captured live camera vectors. Earlier base-selection recovery at08002CB4..08002CF0, offset-vector generation at08002CF2..08002D06, and later root/alternate branching remain outside this function. Those are the next dependencies before coherent intermediate-pose visibility and live scene/object integration. Archived native source/header/test/report and updated VISIBILITY.md. Full-scene60fps gameplay remains unverified; ROM, saves, stable fallback and original timing remain unchanged.

## 2026-09-24 continuation: native visibility offset generation

Recovered the ROM seed at08615F08 as(8,0,80), transformed by the12-word affine matrix supplied at caller stack+98. Added nfs_visibility_offset for Thumb08002CF2..08002D06 / transform0806DEC0: fixed14 wrapped dot products followed by translation, yielding integer XYZ. This is original visibility-query arithmetic, not screen-polygon interpolation or continuous camera reconstruction.

Added test_visibility_offset.py:1,000 original-Thumb comparisons pass, including500 full-width wrapping cases and500 ordinary fixed14 matrices; invalid input preserves output. Added test_visibility_offset_pair.py: all276 extended original-sequence comparisons (08002CF2..08002D92) match generated XYZ, both selected regions and all256 final state bytes. Each of69 retained worlds uses one retained camera matrix and three explicit synthetic matrices. Original execution takes180 fallback calls,177 keep-previous decisions and163 opposite misses. All64 injected read failures preserve state/results. Warnings-as-errors build and69 root-plus-builder comparisons pass.

These fixtures do not assert the retained camera matrix is the exact matrix originally supplied at stack+98. Next dependency: capture that complete sequence with its actual matrix, recover earlier base-selection behavior and later root/alternate branching, then intermediate-pose visibility and complete scene/object live integration. Archived source/header/tests/reports and updated VISIBILITY.md. Full-scene60fps gameplay remains unverified. ROM, saves, stable synchronized fallback and original timing are unchanged.

## 2026-09-24 continuation: actual matrix plus selection sequence verified

Added nf_visibility_pair_capture to the opt-in diagnostic bridge. It captures Thumb08002CF2 entry through08002D92 exit, using r10 for the world-state address and retaining full register/RAM snapshots. This preserves the exact caller stack+98 matrix pointer and the inputs/outputs of offset generation plus both region searches. Existing capture modes and ordinary bridge remain unchanged.

Added test_pair_capture.py with a completed-capture manifest. All24 actual sequences from an850-refresh scripted route match native offset XYZ, both selected regions and all256 final world-state bytes. Captures contain22 distinct offsets; the actual matrix resides at03005EC0. Observed pairs are(22,22),(87,87),(88,88). These captures therefore establish exact live-matrix composition for same-region pairs, not differing-side/root branches. Paired ordinary-bridge control preserves all206 scene-packet hashes and final EWRAM/IWRAM/VRAM. Regression checks retain24 exact local transitions and69 root-plus-builder matches.

This removes the previous uncertainty about using a substitute camera matrix in the composed test. It does not recover how03005EC0 is constructed for a new intermediate rigid pose. Raw snapshots remain private in work/camera/pair-corpus; archived capture source/test/report/manifest and updated VISIBILITY.md.

Next dependency: earlier base-region recovery, later root/alternate branching (especially differing region pairs), and mapping rigid camera poses to the visibility-query matrix. Then complete coherent scene/object visibility and live renderer integration. Full-scene60fps gameplay remains unverified. ROM, saves, stable synchronized fallback and original simulation timing remain unchanged.

## 2026-09-24 continuation: native base recovery and query composition

Added nfs_visibility_query for original Thumb08002CB4..08002D92. It initializes the query state from the stored region and fixed8 base point, runs the preliminary local search, replaces the stored region with the supplied recovery region only onFFFF, generates the transformed offset and performs paired selection. A successful preliminary neighbor result deliberately does not replace the stored region, matching the original. State, stored region and both results publish atomically. Recovery source (original caller object+78) is supplied explicitly; the object ownership/selection is outside this function.

Added test_visibility_query.py. All276 original-Thumb sequence comparisons pass across69 captured worlds and four explicit matrix/base fixtures. Cases include138 preliminary recovery branches,207 paired fallback calls and207 keep-previous decisions. Both results, stored-region global and all256 final state bytes agree. All98 injected read failures preserve state, stored region and result outputs. Warnings-as-errors build passes. Existing24 actual matrix/paired-selection captures and69 root-plus-builder comparisons remain exact.

Archived native source/header/test/report and updated VISIBILITY.md. Next dependency: later root/alternate-region branching for equal/differing pairs, plus actual full-query capture and recovery-object provenance. Continuous-pose matrix construction and complete coherent scene/object live integration still remain; this is not verified full-scene60fps gameplay. ROM, saves, stable synchronized fallback and original timing are unchanged.

## 2026-09-24 resumed: root branch choice verified

User resumed work and explicitly resumed continuation; existing every-minute heartbeat is ACTIVE again, with its prompt and notification behavior preserved. No duplicate automation was created.

Added nfs_visibility_choose_root for Thumb08002FEA through the common builder dispatch. It chooses the first region unlessFFFF, then the opposite, updates the stored unredirected region and applies descriptor+22 to the initialized root index while retaining other root bytes. Equal/differing branches both dispatch the same builder. Invalid pairs, absent-both and read failures publish neither output.

Added test_visibility_choose_root.py. All552 original-Thumb branch comparisons pass across69 retained worlds, four explicit region pairs and two descriptor-redirect fixtures. This includes276 synthetic redirects, equal/differing choices, absent-first and absent-opposite. Both the chosen global region and all16 root bytes agree; both branches dispatch the same original builder index and state pointer. Three failure cases preserve outputs. Fixture changes are confined to oracle memory, never the ROM file. Warnings-as-errors DLL compilation and all69 existing root-plus-builder comparisons pass.

Archived native source/header/test/report and updated VISIBILITY.md. Next dependency: coherent full-query/root/builder composition with actual input capture, recovery-object provenance, and mapping intermediate rigid poses to the query/view matrices before live scene/object integration. These are native visibility component checks, not verified full-scene60fps gameplay. ROM, saves, stable synchronized fallback and original timing are unchanged.

## 2026-09-25 continuation: atomic pair-to-queue composition

Added nfs_visibility_build_pair, composing retained viewport root initialization, region-pair choice/redirect and the complete native builder. It rebuilds the initial root instead of requiring captured root bytes, preserves unused queue records, and publishes state256, queue320, membership4096 and selected region together only after all stages succeed. This provides one transactional native boundary for later snapshot integration; pair calculation remains external.

Added test_visibility_build_pair.py. All69 captured worlds match the original final state, full queue and full membership table for four supplied pair variants each (276 comparisons). Tests deliberately poison the input root bytes to establish reconstruction. All1,221 individual snapshot-read failure injections preserve all four outputs, including failures after successful root choice. Absent-both pair failure also preserves outputs. Warnings-as-errors compilation and552 original-Thumb root-branch comparisons pass.

The pair variants are explicit fixtures consistent with each capture's chosen region; this does not yet establish temporal coherence from the earlier query through builder inputs, or intermediate-camera visibility. Next dependency: actual full-query-to-builder capture and a retained snapshot containing the matching query/view matrices and geometry before full scene/object live integration. Archived source/header/test/report and updated VISIBILITY.md. Full-scene60fps gameplay remains unverified. ROM, saves, stable synchronized fallback and original timing are unchanged.

## 2026-09-25 continuation: coherent query/builder capture reveals matrix reuse

Added nf_visibility_pipeline_capture in the opt-in diagnostic bridge. It retains four boundaries from one update: query input08002CB4, query output08002D92, builder input03004C74 and builder output03004D50. This mode reports4 complete and5 error, with0..3 pending stages. Other capture modes retain their existing status behavior. Added test_pipeline_capture.py and completed manifest.

All24 coherent sequences match native full query results/stored region/state and native pair-to-builder final state/queue/membership. Same scene serial is verified across all four boundaries. Paired ordinary-bridge run preserves all206 packet hashes and final EWRAM/IWRAM/VRAM. Prior24 actual pair-capture comparisons also pass. The actual recovery object in these samples is02004458, with region read from+78; object ownership outside this capture remains to be traced.

The coherence audit found no changed query-geometry reads, no changed world-state bytes between query output and builder input, and no changed unused queue tail. However, every sample has one changed builder input: the48-byte matrix at03005EC0. The query sees rotation with zero translation; builder sees changed rotation entries and added translation. Example first sample changes matrix entries2/6 from15160/-15160 to-15160/15160 and translation from0,0,0 to9041,100,-2071. This establishes that the same address is reused for distinct query/view transforms; a snapshot cannot blindly serve the query-time matrix to the builder.

Next dependency: recover and verify this interstage matrix conversion, then compose the native stages from one retained snapshot or explicitly version the two matrices. No claim of a single fully native query-to-builder pipeline yet. Raw four-boundary snapshots remain private under work/camera/pipeline-corpus; source/test/report/manifest and VISIBILITY.md are archived. Full-scene60fps gameplay remains unverified; ROM, saves, stable fallback and original timing are unchanged.

## 2026-09-25 continuation: native visibility view-matrix construction

Traced interstage setup: Thumb08002E56..08002E68 regenerates yaw via0806DD04;08002EAC..08002EC4 writes negative camera X/Y/Z translation. This is a rebuild from selected yaw/position, not safely assumed to be a generic inverse of the prior query matrix. Y includes a16-unit adjustment and a fixed8 camera offset; earlier camera-mode/height decisions remain separate.

Added nfs_visibility_view_matrix using the original8192-sample signed half-sine table (retained from the user's ROM) and14-bit angle wrap. It generates all12 matrix words, with original unsigned wrapping for negation/translation. Added test_visibility_view_matrix.py. All16,384 possible angles match original Thumb yaw construction plus translation stores, using full-width translation fixtures. All24 actual builder matrices from the coherent pipeline captures are byte-identical when supplied their recorded final angle/position inputs. Warnings-as-errors build and276 composed pair-to-builder cases with1,221 read-failure checks pass.

This recovers matrix arithmetic, not the policy choosing the final camera position/angle. The actual-capture comparison uses those recorded inputs explicitly. Next dependency: recover that interstage input policy (camera mode/height/yaw adjustments) or retain its complete coherent inputs, then native single-snapshot composition and intermediate rigid-pose rendering. Archived source/header/test/report and updated VISIBILITY.md. Full-scene60fps gameplay remains unverified; ROM, saves, stable fallback and original timing are unchanged.

## 2026-09-25 continuation: native single-snapshot visibility evaluation

Added nfs_visibility_evaluate, composing base recovery, offset/paired queries, root choice and the complete queue builder. It reads one immutable snapshot throughout. The query uses the original reader; the builder uses a bounded reader overlay for its separately supplied48-byte view matrix at state+54's address. The overlay copies data to the requested output only, never mutating snapshot RAM. State256, queue320, groups4096 and selected region publish atomically. Caller must supply intended viewport/projection setup and explicit query/view matrices; camera-input policy remains external.

Added test_visibility_evaluate.py. All24 actual four-boundary captures reproduce original final state, full queue, membership and selected region with every underlying memory read served only from query-entry RAM. The view matrix is explicitly taken from the matched builder boundary. All552 read-failure injections preserve all four outputs. Negative control supplying the query matrix as the view matrix changes/fails21 of24 cases, demonstrating the version distinction is materially tested. Warnings-as-errors compilation and276 pair-to-builder comparisons with1,221 failure checks pass.

This is a native query-to-queue component milestone using a retained snapshot plus versioned camera inputs; it is not recovery of camera-input policy, complete scene/object rendering or verified60fps gameplay. The sampled viewport/state setup needs no interstage changes, but other camera modes are not covered. Next dependency: retain a bounded scene snapshot with both matrix versions and complete required world/object inputs, then evaluate intermediate rigid poses and integrate the live renderer. Archived source/header/test/report and updated VISIBILITY.md. ROM, saves, stable synchronized fallback and original timing remain unchanged.

## 2026-09-25 continuation: owned visibility snapshots

Added visibility_snapshot.c/h. A visibility snapshot owns288 KiB of captured EWRAM/IWRAM plus query inputs and both matrix versions. Reference-counted assets own one bounded ROM copy (maximum32 MiB) shared across snapshots; callers can release their asset reference before evaluating retained snapshots. No live-emulator buffers are borrowed. Reads are bounded to explicit EWRAM/IWRAM/ROM ranges; cross-region and overflow-sized requests fail without modifying destinations. Evaluation produces the native final state/queue/groups/selected result transactionally. Lifetime operations are explicitly single-owner, not thread-safe.

Added test_visibility_snapshot.py and built visibility-snapshot.dll separately with warnings as errors. All24 retained snapshots match original final results, including48 repeated evaluations after deliberately overwriting source RAM/matrices/base/ROM input buffers and releasing the caller's asset handle.147 invalid ranges/creation cases fail safely; an invalid retained queue pointer preserves the complete result buffer. Initial compiler indentation warning was corrected before the successful strict build.

This is ownership infrastructure for visibility data, not a complete render snapshot: VRAM, scene render packets, materials/textures and full object content are not included. No live sink integration yet. Next dependency: attach/version this data with scene epoch and boundary identity under the existing snapshot budget, then connect world/object rendering and evaluate intermediate poses. Archived source/header/test/report and updated VISIBILITY.md. Full-scene60fps gameplay remains unverified. ROM file, saves, stable fallback and original timing are unchanged.

## 2026-09-25 continuation: scene identity guards for visibility snapshots

Added NFVisibilityIdentity and bind-once/check-before-evaluate APIs to visibility_snapshot. Identity includes reset epoch, scene serial, packet begin/end refreshes and ordered query/builder refreshes. Binding requires a nonzero epoch and timestamps inside the packet's bounds. Checked evaluation rejects unbound snapshots or mismatched epoch, scene or packet bounds without modifying output. Existing unguarded evaluation remains explicitly available for component diagnostics; live consumers must use the checked API. The caller is responsible for deriving identity from verified capture/packet metadata.

Extended test_pipeline_capture.py to record packet identities from the actual scene sink. Added test_visibility_snapshot_identity.py: all24 retained visibility captures match an actual packet's epoch/serial/bounds and still reproduce original results.168 guard checks cover unbound use, invalid timing, rebinding and individual epoch/serial/bound mismatches. Existing ownership checks also pass:48 repeat evaluations after source buffers are overwritten/caller ROM handle released,147 invalid ranges/creation cases and atomic invalid-queue failure. Strict DLL build passes; capture noninterference retains206 identical scene packets and final RAM.

This prevents accidental cross-scene/reset consumption when the checked API is used. It does not yet attach snapshot payloads to the live scene sink or enforce aggregate retention budgets; those are next before rendering integration. Full render assets/object visibility and intermediate poses remain unfinished. Archived source/header/tests/identity report and updated VISIBILITY.md. Full-scene60fps gameplay remains unverified; ROM, saves, stable fallback and original timing are unchanged.

## 2026-09-25 continuation: bounded owned visibility history

Added NFVisibilityHistory APIs to visibility_snapshot. History retains owned copies of bound snapshots, at most16, with a configurable byte budget accounting for the history object, its snapshot copies and one shared ROM allocation. External snapshots and a temporary incoming clone allocation are explicitly outside that retained budget. Insertion validates identity/asset consistency and ordering before mutation, rejects duplicate/older scenes or epochs, evicts oldest at capacity, and clears prior entries on a newer epoch. Evaluation requires matching packet identity and returns copied results, never borrowed history pointers.

Added test_visibility_history.py. A two-entry8,978,920-byte budget retains24 actual captured snapshots with22 checked evictions; usage never exceeds the budget. Duplicate/out-of-order insertion, undersized budgets and stale epochs are rejected. New-epoch insertion clears old lookup results. The final two entries remain exact after source snapshots and the caller asset handle are destroyed. Identity/lifecycle regressions also pass:168 identity guards,48 repeat evaluations,147 invalid ranges/creation checks and atomic invalid-queue failure. Strict DLL build passes.

This budgets visibility history only; it is not yet attached to live scene packets or combined with their render-asset budget. Next dependency: opt-in live capture/attachment with matching scene identity and paired retention, followed by full object/world visibility and intermediate-pose rendering. Archived source/header/test/report and updated VISIBILITY.md. Full-scene60fps gameplay remains unverified; ROM, saves, stable fallback and original timing are unchanged.

## 2026-09-25 continuation: opt-in live visibility attachment milestone

Added live_visibility.h under NF_VISIBILITY_CAPTURE only. The research bridge can enable owned ROM assets and a bounded visibility history, capture query-entry RAM/inputs and builder matrix versions on every update, evaluate the native pipeline at the builder exit, and compare all original state/queue/membership/selected bytes before accepting a pending snapshot. At scene publication it binds matching epoch/serial/refresh bounds and retains the owned snapshot before delivering the unchanged packet. A dedicated evaluation API reads only owned history and rejects stale epochs immediately after discontinuity. Resets clear pending captures; close releases assets/history. Original game rendering, timing and ordinary nfsprobe.dll remain unchanged.

Updated the diagnostic build to link native visibility/snapshot sources. Added test_live_visibility.py. Across850 scripted refreshes:207 query candidates and207 exact native results, zero rejected,206 completed scene packets with206 retained/evaluable attachments, zero missing. One final candidate awaits a completed scene. Paired ordinary bridge preserves all206 packet hashes and final EWRAM/IWRAM/VRAM. The test overwrites the caller ROM buffer after enabling and verifies stale-epoch rejection after reset. Existing24 four-boundary capture checks also pass with live attachment disabled.

This is a live data-attachment milestone, not live native drawing: the renderer does not yet consume attached visibility or evaluate intermediate poses. Visibility retention has its own16 MiB test budget; render-packet retention remains separate. Next dependency: expose retained geometry/region results to native world/object rendering and evaluate coherent intermediate rigid poses, with camera-mode/viewport coverage beyond this scripted run. Archived live header, bridge/scene hooks, build script, test/report and updated VISIBILITY.md. Full-scene60fps gameplay remains unverified; ROM file, saves, stable fallback and original timing are preserved.

## 2026-09-25 continuation: retained visibility at explicit changed poses

Added NFVisibilityPoseInputs and nf_visibility_snapshot_evaluate_at. The checked API requires matching epoch/scene/packet bounds and accepts an explicit coherent base/query/view input set, evaluating from retained world data without mutating the original snapshot. Refactored shared evaluation so ordinary captured-pose evaluation retains identical behavior. Pose construction/interpolation remains the caller's responsibility; no projected-polygon matching or game timing changes are introduced.

Added test_visibility_pose.py. Across24 actual retained scenes,72 coherent X-translation fixtures (-8,0,+8 world units) match original Thumb query and root branching plus original ARM builder execution byte-for-byte in state/queue/groups/selected.34 fixture queues differ from their original captured pose, demonstrating the override affects visibility; zero-offset cases equal original captures. Evaluating the original snapshot again remains exact, and stale-epoch pose evaluation is rejected without touching output. Existing168 identity guards,48 repeat evaluations and147 invalid-range/creation checks also pass. Strict DLL build passes.

The oracle supplies original viewport setup and explicit translated matrix/base inputs; this is not continuous quaternion interpolation, camera-mode policy recovery, world/object draw-list regeneration or displayed60fps validation. Next dependency: generate coherent query/view inputs from the rigid presentation pose and connect these visibility results to retained world/object geometry. Archived source/header/test/report and updated VISIBILITY.md. ROM, saves, stable synchronized fallback and original timing remain unchanged.

## 2026-09-25 continuation: native world-queue draw order

Recovered outer world dispatcher03004D5C..03004DFC and added nfs_visibility_draw_plan. It emits bounded(queue index,pass) pairs: reverse queue order in pass0 excluding flag8, then reverse order in pass1 excluding flags8/80. At most40 region draws are emitted from20 queue records. Capacity/invalid-input failure leaves the output plan/count unchanged. This exposes verified order to a future native region consumer; it does not yet draw surfaces.

Added test_visibility_draw_plan.py. All69 actual captured final queues and105 explicit flag/count fixtures match the original dispatcher call sequence to030027F0 (1,705 total calls), including zero-count and suppressed-record cases.128 insufficient-capacity tests preserve output. The oracle stubs global draw-scratch clear03005224 and region-draw leaves, so the test claims dispatch order/filtering only. Strict native DLL compilation passes.

Next dependency: translate the030027F0 region consumer into retained world/material draw commands, then connect those commands to native surfaces and handle object-generated regions. This is necessary before visibility changes can reveal newly visible geometry in the live renderer. Archived source/header/test/report and updated VISIBILITY.md. Full-scene60fps gameplay remains unverified; ROM, saves, stable fallback and original timing are unchanged.

## 2026-09-25 continuation: native region material gate and clipping setup

Added nfs_visibility_region_setup for030027F0..030028C8. It resolves the48-byte region descriptor, checks optional20-byte material metadata at descriptor+0A for hidden flag40, identifies the68-byte geometry-ring address/count and prepares signed viewport bounds plus state+E2..E8. Hidden/invalid/unavailable paths leave all outputs untouched; successful output publishes state, viewport, descriptor and geometry together. This is the setup boundary before recursive chains and surface/object drawing.

Added test_visibility_region_setup.py. Across480 region records from69 captured final queues, both explicit synthetic material states compare with original ARM:480 prepared cases match all256 state bytes,16 viewport bytes, descriptor and vertex address/count;480 hidden cases leave outputs unchanged and follow the original early return. A read failure is atomic. Strict native DLL build passes. These tests deliberately override material flags in isolated oracle memory; they do not claim all hidden cases occurred during gameplay.

Next dependency: region geometry transform/culling03000D48 and wall/road command generation03001800, including recursive descriptors and object passes, so the native renderer can draw geometry newly exposed by a changed pose. Archived source/header/test/report and updated VISIBILITY.md. Full-scene60fps gameplay remains unverified; ROM file, saves, stable fallback and original timing are unchanged.

## 2026-09-25 continuation: native region geometry scratch transform

Added nfs_visibility_region_transform for03000D48..03000EF8. It transforms68-byte world vertices into52-byte scratch edges using the retained camera matrix, optional signed material X/Z/top/bottom offsets, original integer wrapping, height fields and intensity seeds. Successful rings link each edge endpoint cyclically. Original far-depth rejection returns0 after partial scratch writes; that observable behavior is preserved. Invalid inputs/read failures return-1 with no scratch publication.

Added test_visibility_region_transform.py. All480 region rings from69 captured queues match original ARM scratch bytes and return values. Those actual records contain no material offsets or far stops, so eight explicit synthetic material/depth fixtures supplement them. All488 comparisons pass:485 completed rings and three far stops, including threshold and signed-height behavior.480 injected snapshot-read failures preserve scratch; inputs remain unchanged. Strict DLL build passes.

This supplies transformed region data but does not yet emit or draw walls/roads. Next dependency: translate wall command traversal03001800 and surface/material resolution, then recursive descriptors and object passes, and connect the result to native renderer surfaces. Archived source/header/test/report and updated VISIBILITY.md. Full-scene60fps gameplay remains unverified; ROM file, saves, stable fallback and original timing are unchanged.

Wall scratch UV: nfs_visibility_wall_uv reproduces03001A7C..03001B0C with explicit resolved material/U/V inputs. Verified against original ARM in1,040 synthetic arithmetic fixtures; material lookup, clipping and projection remain outside this API. It changes six UV words and flags only, retaining all other scratch bytes.

Wall material preparation: nfs_visibility_wall_prepare resolves state+20 wall materials, state+48 animated UV offsets and optional state+18 endpoint height offsets, then composes wall_uv. Outputs publish atomically after successful reads. Original ARM comparison:512 synthetic cases,1,536 injected failed reads; clipping/projection and independent interpolation fields remain outside this API.

Near wall clipping: nfs_visibility_wall_clip implements03001B0C..03001CA0/helper1638, including signed-word times unsigned fixed24 factors. Input attributes are source+20/+24 in currentA,currentB,nextA,nextB order. Both-behind leaves outputs unchanged and returns0; caller must later apply rejection flags24. Verified1,600 synthetic original ARM comparisons across all endpoint classifications. Projection and rendered full scenes remain pending.

Wall projection: nfs_visibility_wall_project reproduces03001CB4..03001FA8 with surface vertex emission excluded. Projects X/heights, handles orientation and horizontal viewport rejection;1,600 original ARM synthetic comparisons pass. This exact integer diagnostic stage retains original quantization and is not itself a native4K precision solution. Complete ring composition and surface vertex generation remain pending.

Region wall composition: nfs_visibility_region_walls traverses a transformed cyclic ring, combining material/UV, clipping and projection with atomic publication. All wall scratch bytes match complete original03001800 execution for480 captured rings/2,628 edges. Surface vertex stream and state+F2 remain unimplemented outputs; native transform is separately verified. Test injects480 initial read failures.

Surface vertices: nfs_visibility_surface_vertices emits the optional clipped-start and required end vertex, including affine/perspective texture fields. Affine intentionally preserves reciprocal slots.1,024 original ARM synthetic comparisons and1,024 atomic capacity checks pass. Complete region composition/count publication remains pending.

Complete region geometry: nfs_visibility_region_geometry composes wall scratch, surface vertex stream and state+F2 publication from transformed rings. Captured verification:480 regions,2,628 wall edges,1,852 surface vertices, full state/stream/scratch equality with original03001800. Read/capacity failure preserves all outputs. Region recursion and drawing are outside this API.

Single-region reconstruction: nfs_visibility_region_reconstruct composes setup, ring reads, transform and geometry in an atomic wrapper.480 captured regions match with native transform included. Returns0 hidden/far without exposing partial scratch; returns-1 for failure. Does not dispatch recursive/object/material drawing. Visibility snapshots lack palette memory required by native_surface extraction.

Wall draw plan: nfs_visibility_wall_draw_plan recovers0300264C filtering, reversed-edge deferred pass and animated material resolution. Outputs edge/resolved descriptor/texture/dimensions/source flags without rasterization.512 synthetic ARM dispatch comparisons cover781 leaf calls. Captured scene validation and native surface construction remain pending.

Captured wall dispatch validation:960 diagnostic invocations across480 regions match1,578 intercepted raster leaves;4,984 read-failure and810 capacity-failure checks preserve outputs. A returned zero deferred mask causes the second diagnostic invocation to repeat initial dispatch, so these totals are not unique game draw counts. No raster/pixel comparison is performed.

Optional BG palette retention: snapshot_set_palette owns512 bytes at05000000 and must precede identity binding. Absent palettes fail reads, repeated sets fail, history budget includes storage.24 synthetic-palette/captured-visibility ownership tests pass. Live palette capture and temporal coherence remain pending.

Live palette audit: builder-exit BG palette compared at wall/road draw entries and packet publication.850 refreshes produced207 captures/4,476 checks/2,847 mismatches; only1 palette attachment accepted. Visibility206 packets still exact/retained with baseline game output unchanged. Need palette versions per draw/material, not an assumed scene-wide stable palette. Boundary checks are not a memory-write trace.

Draw-boundary palette detail:207 scenes,2,436 draw samples different from first draw,149 first-draw/builder mismatches,124 publication/first-draw mismatches.64-entry diagnostic dedup finds maximum20 unique palettes with zero overflow. Need per-draw palette retention; changes in unused palette entries have not yet been distinguished from texture-used colours.

Owned draw palettes: draw_palette.c/h provides scene epoch/serial plus draw ordinal/kind/source/material identities,64 deduplicated palettes,256 draws,36,888 bytes. Seal before reading; owned and immutable after publication.256 synthetic ownership/dedup/capacity cases verified; live attachment pending.

Live draw-palette banks now retain16 completed scenes plus one pending; lookup guards epoch/serial/packet bounds/ordinal.850-refresh test retains206 banks/4,234 readable draw palettes with zero failures and190 evictions; original game output remains exact. These are draw-entry palette bytes; other draw-time material/lighting memory versions still need retention/validation before extraction.

Surface-read audit (opt-in):4,270 successful live extractions request36,828 ranges.24,018 match retained query snapshot;8,540 changed reads are world state256 plus temporary material48;4,270 unavailable reads are BG palette512. Other requested texture/lighting/geometry bytes match for this route. Next: compact state/material overrides with palette and retained-only extraction parity.

Retained-reader parity:4,270 wall/road surfaces and lighting outputs match live extraction byte-for-byte using owned query RAM/ROM plus copied state256/material48/palette512 overrides. Overrides currently live only during immediate audit; deferred history storage remains pending. No live memory reads inside the retained callback.

Deferred audit now regenerates surfaces at completed packet publication using saved draw arguments/state/material/palette overrides and retained snapshot.4,234 surface/lighting length+FNV64 comparisons pass; zero failures/overflows. Storage is pending-scene only, discarded at reset, not yet persistent history ownership.

Completed surface audit retains two owned scene snapshots plus draw overrides, rebinding readers after clone.1,686 later-frame regeneration checks pass; FIFO eviction rejects stale entries. Cache is research-only and separate from existing budgets, with one incoming allocation peak; no displayed renderer integration yet.

Completed extraction API now returns caller-owned surface/lighting from matching scene ordinal after retained-only reconstruction and fingerprint checks.206 retrievals pass; returned allocation survives eviction/reset. Release via nf_surface_free. Research two-slot cache/audit must be enabled; no display integration yet.

Diagnostic GPU milestone:206 packets rebuilt from owned-history world surfaces/lighting match original packet bytes. Existing packet-preview renders pair204/205 at3840x2160,alpha0.5 with zero lighting fallback. Captured model/order/identities remain in use; this does not yet generate newly visible world geometry or establish full-scene60fps.

Live wall-plan audit:2,179 original264C intervals/3,202 wall leaves match native command order/material/texture/dimensions/flags and deferred masks with zero failures. Uses original current scratch; untraced direct wall entries and full native region scheduling remain pending.

Live composed geometry:1,913 region calls match state/scratch/surface outputs; native scratch supplies all2,179 verified wall-plan invocations/3,202 leaves. Setup and recursive scheduling remain original; initialized scratch inherited. Diagnostic reads reciprocal ROM per region and is not a paced renderer.

Region child links: flag8 uses ordered+24 chain replacing own draw; otherwise+6 is post-surface child.66 synthetic original ARM fragment comparisons pass; cycle fails atomically. Hidden/transform gates and full recursive drawing remain caller responsibilities.

Captured link tests:480 regions match original scheduling fragments;22 actual+6 children,zero flag8 replacement regions.24 atomic capacity/read failures include failure after an earlier successful child read. Full recursive traces and replacement-mode real coverage remain pending.

Live nested region trace:3,523 entries,96 descriptor+6 child calls,194 object-generated region calls(return03002364),maxdepth2,1,610 nonzero-pass entries. Zero linked-child mismatches after distinguishing object calls. No real flag8 replacement chains; object-region dispatch remains to reconstruct.

Object-region helper reproduces flag10 branch: object+36 region,state E2..E8 bounds,flags/depth0,parentFFFF.512 ARM fixtures pass plus non-region/invalid guards. No camera transform change in this branch; full object list dispatch remains pending.

Live object-region helper:194 record/pass comparisons exact.191 full object blocks differ from query snapshot, but flags+0A and region+36 match in all194. Other changed object fields still require analysis before native list scheduling.

Object field audit:positions stable across194 observed region objects;distance+28 changes191 times,next-link word+04 six times,three other words once. Native object_distance reproduces planar camera transform/wrapped squared distance in1,024 ARM fixtures; list scheduling still pending.

Live object distance audit:468 exact X/Z/distance register+memory comparisons,68 nonpositive-depth cases,zero failures.400 forward candidates reach ordering; insertion/link behavior still pending.

Object insertion helper: descending signed distance, new equals precede old,FFFF tail.1,024 original ARM sequential insertions and32 duplicate atomic rejections pass. Caller supplies object array and computed distance; live bounds/traversal/callbacks pending.

Live insertion:400 full-prefix/head/maximum comparisons exact,max observed prefix26 objects. Original linked nodes determine bounded capture prefix; this does not recover total array capacity. Source-list visitation/callback gates remain pending.

Object visit helper marks first visits even inactive,skips repeats,selects callback+4E only(flags+08&3)==1.1,024 ARM fixtures match bitmap/disposition/selector. Callback effects remain external; reread flags before sorting.

Live visitation:427 exact bitmap/disposition decisions,296 active,131 skipped,142 callback selections;zero failures. Original callbacks remain external.850-refresh control preserves206 packets and final RAM. Source-list traversal and composed native dispatch remain pending.

Correction2026-09-26:03002018 is first-node entry only;030021F8 reads next object+02 and loops03002020. Audit now covers all1,801 visits (468 active,1,333 skipped,262 callbacks), all exact. Prior427 count covered first nodes only. Future native traversal must read next link after callback/processing.

Native source cursor consumes post-processing object+02, independent of global visit bitmap and sorted+04.130 original ARM list fixtures/8,384 nodes exact; link mutation respected, malformed cycles/ranges fail atomically. Inactive-object fixtures isolate traversal; callback/resume and ordering composition pending.

Live cursor audit:427 complete lists,1,801 indices/advances exact,zero failures or reentrancy observed. Uses256 diagnostic bound; original processing remains authoritative. Native collection composition and wider coverage pending.

Post-callback sort composition:flag4 gate,distance write including behind-camera cases,positive-depth insertion.1,024 original ARM comparisons (391 insertions,633 skips) exact; invalid insertion rolls back distance. Live composition and callback handoff remain pending.

Live post-callback sort composition:468 full-prefix/head/maximum matches,zero failures,max prefix26.400 insertions/68 depth skips; disabled-flag skips only synthetic so far. Original callbacks and processing still authoritative.

Collector coordinates visit/callback request/resume/sort/traversal.128 full ARM lists,558 synthetic callback handoffs,2,570 native steps exact across arrays/bitmap/head/maximum/order. Caller supplies callback effects; invalid errors are terminal, not whole-list rollback. Live full-list integration pending.

Live whole collector mirror:427 lists/1,801 visits/262 observed callback handoffs exact. Callback object/bitmap deltas and current matrix/head/maximum supplied from original execution; no callback reexecution.256-record diagnostic window is not allocation proof. Full native rendering dispatch and independent replay pending.

Callback effects audit:262 callbacks,one changes diagnostic object window (four bytes);bitmap/matrix/head/maximum unchanged. Unmeasured memory and side effects remain unknown; callbacks must not be bypassed based on this result.

Callback delta localization:selector12/object24 at020053B8 changes its +32/+33 bytes to88/38,+4A to01,+88 toFF. These belong to the callback object,not unrelated window memory. Meanings and external side effects unrecovered. Four logged bytes,zero overflow;427 complete lists still exact.

Checked callback object delta application verifies pending index/selector,old bytes,ranges and duplicate offsets before writes.558 synthetic outcomes/128 full ARM lists pass;2,232 atomic rejection cases. Scene identity/retention and non-object effects remain external.

Live collector now applies callback object changes through checked deltas:262 applications,427 whole lists exact,zero failures.261 records empty,one four-byte record. Scene-bound retention/detached replay remain pending.

Detached collector replay from owned initial bytes and callback outcomes passes427/427 lists,zero overflow. Replay function has no emulator reads. Current-list buffer only; historical scene identity and pose-dependent matrix policy still pending.

Callback replay preserves unchanged matrix lanes,applies changed lanes only with old-value check.128 ARM lists with558 matrix-changing callbacks pass;427 captured-pose live replays unchanged. Captured head/maximum/bitmap replacement still prevents claiming alternate-pose replay.

Replay now preserves unchanged bitmap/head/maximum,applying only checked callback changes.427 live replays exact.128 ARM collector fixtures with callbacks mutating all these globals pass;changed-global replay branch still needs isolated coverage. Initial sorted state remains captured-pose dependent.

Callback global-state replay extracted to atomic core helper:all changed bitmap/matrix/globals validated before writes.92 field cases plus late failure pass;427 live replays unchanged. Object-delta application remains separate transaction.

Sorted-object draw setup2284..2320 reproduced:camera XYZ,horizontal bounds inherited from region,vertical bounds unchanged.1,024 randomized ARM fixtures exact. Non-region depth/vertical gate and material dispatch pending.

Live draw setup:400 exact XYZ/full-state results,194 region and206 non-region objects. No failures;427 detached list replays preserved. Non-region visibility/material/drawing still original.

Non-region gate2368..23B8 reproduced:unsigned depth<8192 plus projected vertical center/radius bounds.2,048 ARM fixtures exact (679 visible/1,369 culled),including depth0 and wraparound. Live/material dispatch pending.

Live non-region gate:206/206 decisions exact,all visible on this route. No live culled examples;synthetic cases cover rejection.400 draw setups/427 detached list replays preserved. Material/animation and drawing pending.

Object material23B8..2410:base+48 index+animation46/44 offsets and detail selection;flag4 mark.2,048 ARM cases pass after fixing conditionalCMP interpretation (+36 nonzero,including negative). Texture and draw branch pending.

Live material selection:206 exact address/effective-depth/full-object comparisons. No effective-depth overrides observed;synthetic fixtures cover those. Texture and branch resolution pending.

Object texture2410..2460/2588 reproduced:flag8 object pointer with optional previous width*height offset,else material-relative texture.2,048 ARM cases exact across both branches;410 missing-input failures atomic. Draw paths themselves pending.

Live texture/branch:206 exact,all take2588;2460 synthetic-only. Prioritize2588 draw inputs for observed route.400 setups/427 detached replays unchanged.

2588 constructs68-byte model context for4758 (existing live_scene hook2628). Native helper matches512 ARM cases (438 ready,74 slotFF hidden),preserving inherited bytes. Live native-context/extraction connection next.

Live model context:206 complete68-byte contexts/ready decisions exact,zero failures. All ready;hidden only synthetic. Native-context overlay into model extraction is next.

Native reconstructed context overlay feeds206 byte-identical model extractions at45E0. Other reads still live;research assembly still uses original extraction. Guarded substitution and complete owned model inputs next.

Research assembly now consumes verified native context overlay (audit enabled only),guarded by epoch/serial/frame/object/address and one-use token.206 substitutions produce identical scene packets. Other model reads/scheduling remain live;negative lifecycle tests pending.

Assembly guard predicate coverage:1,236 mismatched/consumed-token rejections,zero false accepts;206 actual extractions pass. Tests exercise predicate identities,not malformed extraction or full reset injection. Complete model input ownership next.

Model read inventory:12 ranges/model totaling53,585 bytes;51,200-byte EWRAM texture dominates.206 models/2,472 reads,zero audit overflow. Context/projection/camera/object/palette plus ROM assets need owned versioned capture for detached replay.

Owned model reads:256KiB/128-block bounded capture;205 delayed reextractions match size/hash without emulator reads,zero overflow.206th model pending;one buffer only,scene identity/history/lifecycle still pending.

Owned model flush verifies206th pending capture;206/206 exact. Epoch guard rejects wrong/stale requests and repeated flush is empty. Close invalidates input/token. Unflushed reset and completed history remain pending.

Research assembly now extracts models solely from owned read blocks,guarded by epoch/addresses/rotation and verified context token.206 outputs/packets exact. Live capture and original scheduling remain;completed-scene retention next.

Unflushed reset test passes:pending12 blocks/53,585 bytes immediately invalidated by discontinuity. Current epoch sees empty;old epoch rejects.206 owned assembly outputs preserved. Completed scene history still pending.

Two-slot completed model history binds packet identity after epoch/model-content check.1,686 later-frame reextractions exact;eviction/wrong-end/reset reject. Owns all model inputs;single-model format and fixed256KiB slots,not deduplicated.

Complete retained model+world extraction rebuilds206 packets byte-identically;order/identities/header/reciprocal remain captured. Caller model allocation survives eviction/reset.4K packet-preview pair204/205 exits with19 faces,zero lighting fallback;no new visual QA this turn. Native scheduling/alternate-pose policy pending.

Alternate2460 projected rectangle through24D8 reconstructed:1,024 original-ARM cases exact,invalid depth atomic. Uses object+70 signed size/material dimensions and original wrapping projection. Synthetic coverage only;24D8 onward UV/clipping/draw dispatch remains pending.

Alternate object material/UV selection24D8..252C:1,024 ARM cases exact,92 distant material switches/atomic missing-material rejections. Explicit extents override dimensions when either nonzero; distant condition quarters UV extents and selects next material. Original sb input semantics remain unnamed. Context252C and leaf4EA8 clipping/rasterization next;synthetic-only coverage.

Billboard clip4EA8..5058 reconstructed for positive dimensions<32768:1,600 ARM tests,659 exact accepted setups,933 clipped and8 zero-size rejects. Matches UV clipping adjustments and pair/row increments;output atomic on reject. Unsupported dimensions return-2. Pixel loop5058..50EC and live path remain pending.

Composed billboard prepare projects/selects/clips atomically.1,024 original2460-to-clip comparisons including original context construction:554 accepted exact,441 clipped,29 zero-size. No pixel loop or live alternate-path coverage. New declarations now inside include guard.

Billboard pixel loop5058..50EC reference:512 original-ARM framebuffer matches,512 late-bound failures atomic. Texture zero transparent;writes every other byte from even-aligned x. Material+1A is row shift,not byte stride. Diagnostic original-resolution only;4K renderer/capture integration pending.

Owned NFB1 billboard extraction added:44-byte context plus rectangle/viewport/palette/texture becomes standalone captured-pose RGBA record,index0 transparent. Synthetic fields/32 texels,5 atomic read failures and source-removal ownership pass. Not NSP1-integrated or pose-interpolatable;live2578 capture next.

Research2578 hook now owns latest NFB1 with epoch/serial/frame/object;copy checks epoch/serial,discontinuity/close frees.850-refresh regression206 packets/RAM identical;0 billboard events observed,empty copy atomic. Successful live capture/populated lifecycle untested;single latest slot is not scene completeness.

Shared research billboard capture path populated fixture lifecycle passes:3 captures,wrong identity rejection,failed-read clearing,replacement/reset with independent caller copies. Synthetic reader injection only;CPU2578 natural event still unobserved. Single latest slot remains diagnostic.

NFB1 borrowed decoder validates exact size,dimensions,rectangle/viewport and bounded UV.202 malformed cases atomic;valid texture pointer/fields pass. Out-of-texture UV unsupported. Extraction still raw;renderer integration pending.

Continuous billboard quad helper clips rectangle/UV to viewport and source240x160,then scales to target.3 analytical4K cases,4 outside and4 invalid targets pass. Captured pose only,not original byte-lane rounding or temporal smoothing;GPU consumption pending.

Offscreen billboard GPU helper renders validated NFB1 via existing texture cache at3840x2160. Synthetic clipped2x2 texture readback4 samples verifiesRGB regions/transparent background;one upload. NSP1 ordering/live capture and pose-based motion remain pending.

Billboard GPU isolation fixed upload-before-save texture binding leak;hostile cull/scissor/stencil/fog/lighting/logic/texgen/color-mask/wireframe test passes4K pixels and restoration. Cache miss+hit binding checked. Matrices/active texture remain caller contract.

Extended3,000-refresh driving coverage:721 packets/finalRAM identical to ordinary bridge;billboard events0 at six checkpoints. Current route cannot validate natural2578 capture. Seek different scene/object population instead of assuming synthetic proof is live coverage.

Four alternate saved-state probes x300 refreshes:194 total packets/finalRAM match control,0 billboard events. stage-10 yields0 packets,not render coverage. No distinct-track claim. Stop blind snapshot repetition;prioritize observed model/world native scheduling while billboard natural coverage remains missing.

Owned scene integration now uses native assembler instead of patching captured packets:206 byte-identical outputs,4234 world surfaces,1686 history checks. Packet layout regenerated;captured order/identities/metadata/reciprocal still inputs. Native scheduling pending.

Retained world identity accessor reconstructs road/wall IDs without packet bytes or live reads.4234 identities exact,206 native-assembled packets unchanged. Model identity/command order still captured;identity-failure injection pending.

Model identity now reconstructs from owned context descriptor and captured state/object.206model+4234world IDs exact;all206 assembled packets unchanged. Wrong-end/reset identity outputs atomic. Combined draw order remains captured-packet dependency.

Retained event model slot regenerates206 combined draw orders exactly;native assembler outputs remain exact using recovered identities/order.206 insufficient-capacity failures atomic. Still original draw-event capture,not independent scheduling;complete retained-scene extraction API next.

Whole retained-scene extraction API regenerates206 complete packets exactly from owned histories/ROM. No packet sections/live memory inside API;capture boundary metadata retained. Wrong-end requests atomic. Whole-output eviction/reset lifetime and renderer consumption next;original event scheduling remains.

Whole-scene API lifecycle passes837 eviction rejects/reset and caller-copy survival. API-generated204/205 packets render4K successfully(19faces,2lit,0lightingfallback);preview visually inspected car/road/buildings. Single frame only,no motion proof. Live consumer next.

Live preview --retained consumes whole regenerated packets,compares reference,fail-closed on rebuild error. --reload run96 rebuilt/0failed,342 rendered,1 stale epoch suppressed,0lightingfallback. Unpaced diagnostic only;paced integration/cost measurement next.

Retained timing measured separately:96 rebuilds median2.248ms/max4.341ms;360-refresh total median21.030ms exceeds60fps budget. Simulation/capture median18.920ms dominates,includes audits. Startup render max146ms;not production pacing proof. Cost report/CSV archived.

32-address early event dispatch reduces short retained-preview median21.03->18.27ms;still over60fps budget.850-refresh audit/206packet+RAM parity preserved;static dispatch coverage passes. Ordinary baseline4.02ms vs research-disabled16.57ms indicates substantial remaining instrumentation overhead.

Small32-PC dispatcher separated from noinline heavy handler:retained total median6.178ms,p9511.506ms(previous18.274ms). All850-refresh audits/206packet+RAM parity pass. Current-source nonresearch control4.063ms. Timing headroom improved;paced freshness/motion still unverified.

Paced --retained integration30s:444rebuilt/0failure,1800swaps,1710fresh,79repeat,11startupblank,0skipped,1791simrefresh. Repeats unavailable pair status3;no60fresh-motion claim. Scene-gap latency policy next.

Explicitdelay7 covers tested6-refresh scene gaps:30s1787fresh/0repeat/13startupblank,1800swaps/0skip. Clock test proves simulation unchanged vsdelay5. Adds~33.49ms latency(default still5);visual motion/controller verification pending.

Shared camera/object sampled translation telemetry:10s587fresh;object changes586/586 intervals,camera583/586. Roads/walls/car share camera alpha by source inspection. Input trace only,not full geometry/rotation/perceptual motion proof.

Rotation trace587fresh validates unit quaternions/increasing targets;149pair boundaries show no greater max angular step than437within-pair intervals in tested route. Input pose diagnostic only;geometry/visibility continuity pending.

World identity continuity206scenes:3995comparable draws have0geometry/UV changes,232texture changes;196entries/187exits,5duplicate IDs/10multiplicity changes. Do not collapse duplicates;visibility/material transitions still need classification.

### Duplicate world identity audit (2026-09-27)
The850-refresh continuity audit found all5 duplicate occurrences in scene53:one road andfour walls are exact payload duplicates,including lighting anddimensions. Their draw-command positions differ by10;all10 multiplicity transitions surround this scene(52/53/54). Preserve occurrences andorder:identical surface data does not imply identical compositing effect.3995 comparable adjacent occurrences retain geometry,UV,dimensions andlighting;232texture updates awaitclassification. Next inspect the affected boundary order/visibility,without screen-polygon matching or altering simulation.

### Wall material temporal audit (2026-09-27)
232 wall texture transitions across5identities include68072 transparency changes outof571150 changed texels. Wall alpha is index!=0,independent of palette,so affected updates include index-content/selection changes.141transitions are consistent RGBA remaps and91are not;neither statistic alone identifies raw palette/index provenance. Do not blend these textures merely to increase motion rate:transparent content can ghost. Next capture owned texture pointer/index provenance and preserve source material timing while moving rigid poses continuously.850refresh audit passed;full temporal gameplay verification pending.

### Owned texture provenance (2026-09-27)
Research API nf_live_completed_texture_provenance returns5u64(pointer,width,height,indexFNV64,paletteFNV64) from retained inputs with full scene identity validation andatomic failures.850refresh run:4234reads/206scenes;232RGBA updates include91pointer/91index changes and193whole-palette changes. Dimensions stable.206wrong-boundary failures andreset rejection passed. Whole palette changes may be unrelated to a particular texture's used colors. Next link selected addresses to animation state;no change to material interpolation or game timing.

### Wall frame selection reconstruction (2026-09-27)
Owned nf_live_completed_wall_animation reconstructs state.materials+(wall.base+animation.frame)*32 andstate.texturebase+selected.offset,returning captured address forcomparison.3176wall draws match;1058road rejections and3176wrong-boundary atomic checks pass. Animation118 shows offsets0/1/2;fourteenother sampled entries stay0. Scene refresh bounds do not determine exact animation update instants. Preserve discrete frames;next recover update cadence andvisibility order. Research-only API;original timing unchanged.

### Relative draw-order transitions (2026-09-27)
Identity-order audit includes model marker andexcludes repeated identities at either endpoint.205boundaries yield5pair reversals at52->53(3),60->61(1),140->141(1). Packetfixtures51..55 retained privately for endpoint replay. Extra repeated draws in53 coexist with unique road/wall reordering;do not deduplicate or claim visibility stability. Consumer currently holds older world/order/material while interpolating camera/object poses. Next inspect occlusion at these boundaries;no renderer policy changed.

### Near-boundary visual replay (2026-09-27)
NF_PREVIEW_FRACTION allows finite0..1 single-frame sampling.52/53at.999999 versus53/54at0 renders essentiallysamepose aroundtarget9043. Both4K21faces0lightingfallback. ComparisonPNG shows arrow-sign animation dominates visible differences;road/car appear stable at reducedpreviewsize. Fullsnapshot difference does not isolate order/visibility. Next fixed-material diagnostic plusremaininginversion boundaries. No gameplay60fps conclusion.

### Controlled52->53 boundary (2026-09-27)
Diagnostic packetvariants use exactscene53 camera/objectposes onbothsides andholdshared worldRGBA atscene52values(one changedrecord,no unmatched identities). Geometry,visibility,draworder andduplicates unchanged. Nontexturebytes validated. Two4Krenders match all8294400pixels(0difference),confirming no occlusion jump atthispose aftermaterial isolation. Doesnotjustify deduplication orclaimfullroute smoothness. Next repeat60/61 and140/141.

### Known occlusion discontinuity60->61 (2026-09-27)
Controlled equalposes/sharedworldRGBA:60/61diff149153pixels aroundcarbbox(1587,1314,2054,1755). Pillar switches frombehindcar tocoveringcar. Captured painterorder remainsdiscrete andpose smoothing cannotfixthis.140/141diff7026pixels in distantwallpatch;one newwall identity139937176/base37. Allrenders4K24faces0lightingfallback;notfullsmoothness proof. Prioritize interpolated car/world occlusion orvalidated depthpolicy,without screenmatching orsimulation changes.

### Experimental depth occlusion (2026-09-27)
NF_DIAGNOSTIC_DEPTH compileguard allocates24bitFBOdepth anduseswindowdepth1-1/z withLEQUAL andalphatest. Model/world useactualsampledcamera depths;defaultpainterpath unchanged. Controlled60/61nowpixel-identical0/8294400,previous149153difference. Pillar consistentlycoversthecar. Validateprecision,coplanarity,litwallpasses andtransparentholes beforeliveenable. Wireframepathnotdepthconverted. Bothdepth/defaultbuildscompile;fullgameplayunverified.

### Depth/alpha GPU checks (2026-09-27)
FouractualFBOchecks pass:bothdepthsubmissionorders,transparentfragment preservesdepth,equaldepthredraw;RGBanddepthreadbackverified. Captured204/205 midpointdepthrender19faces2litwalls0fallback. Lighting usesdisjointscissorpalettepasses anddepth-enabledroadvertices. Completiondoesnotprovepixelcorrectlighting. Lifecyclefixture0is205and1is204;chronologicalinputrequired. Nextprecision/coplanarity/performance.

### Depth precision blocker (2026-09-27)
ActualGPUoneunit-separatedplanes nearfirst/farsecond:24bit1-1/z distinguishescorrectly64..4096 buttiesat8192/16384/32767(farwinsLEQUAL). Existing4contractchecks pass;precisiondoesnot. Keepdiagnosticonly. Improveprecision/sharednearpolicy;modelclipsat1worldat64sochangingdepthscalealoneunsafe. Rerunprecision+boundary+alpha afterfix.

### Reversedfloatdepth precision fix (2026-09-27)
DiagnosticdepthnowDEPTH_COMPONENT32F withglClipControl ZERO_TO_ONE,GEQUAL,clear0,vertex-q underorthographicZflip,giving1/z withoutcancellation. Requiresentrypointorreturns29;defaultpainterunchanged. GPU14distances1..1000000 withoneunitseparationallpass;4alpha/order/redrawchecks pass.60/61controlled4Kstill0differences. Nearplanesunchanged. Nextpacedperformance/lighting/clipping;equaldepthcoplanarityunresolved.

### Paced reversed-depth run (2026-09-27)
Separatepaced-depth-preview30s retained/windowbuffer/delay7:444rebuilt0failed,1800swaps1787fresh13startupblank0repeat0skip,1791simrefresh,0lightingfallback/incompatibility/rejection. Render-onlymedian2.3889ms,p953.6367,max7.089;notwholeloopcost. Originaltimingand~117.2mspresentationdelay preserved. Scriptednocontroller;visibilityentrants/coplanarity/clipping stillpendingbeforegameplayclaim.

### Entrant wall isolated (2026-09-27)
Reverseddepth140/141still7026differentpixels. Privatealpha-onlysuppression ofnewwall139937176/base37makescomparison0pixelsdifferent,samepose/sharedmaterials. Thisidentifiesgeometryavailabilitygap,notdepthfailure. Suppressionisdiagnosticonly,no proposedlivefix. Nextretainedcandidatevisibility atinterpolatedpose;olderpacket lackswall.

### Entrant frustum timing (2026-09-27)
Nativecamera projection ofwall139937176:offscreenleftalpha0/.25/.5,overlapsat.75/1;firsthorizontaloverlap0.671377. Depth2774..4251,notnearplaneevent. Capturedolderlistcannotdisplaythewallduringlastthirdofinterpolation. Conservativeboundsnotocclusionproof. Nextboundedownedstaticcandidate replay withmaterial/lifetimechecks andnativeclipping.

### Single entrant candidate experiment (2026-09-27)
Diagnostic140packet addsone141wall withidentity139937176/base37. Depth/viewportclipping yield0changedpixelsalpha0/.5 then1790pixelsleftstripat.75,consistentwithentry. Six4Krenderspass. Futurematerialborrownotvalidlivepolicy;recoverolderownedcandidateinputs beforegeneralizing. No simulationchange orimagebasedinterpolation.

### Earlier candidate inputs (2026-09-27)
Ownedcompleted snapshotcopyAPI(max64KiB,atomicfailure) verifies140alreadyhaswallsource/material/anim37frame0/128x64indices identical141. Genericpaletteabsentbothsnapshots;perdrawpalettesseparate. Do notborrowfuturepalette. Nextresolveearlierpalette+descriptor toextractcompletecandidate. Existingprovenancechecks pass.

### Entrant palette agreement (2026-09-27)
Textureuses59indices.140:12draws4fullpalettes;141:13draws8fullpalettes. All25drawpalettesagreeonthose59entries acrossbothscenes. Earlierpaletteusableforthisunlitcandidateunderexplicitagreementguard;notgeneralpalettereusepermission. Nextowningdescriptor/older-onlyextraction. Auditregressionspass.

### Earlier-owned extraction (2026-09-27)
Nativeextractor reconstructsentrantfrom140ownedbytes/animation/indices/palette andmatchesfull141surfacebyte-for-byte. Descriptoraddress/flagsstilllearnedfrom141event;recoverindependentlybeforelivecandidateenumeration. DiagnosticargumentsAPIidentitychecked.850refreshregressionspass;no liveinsertion.

### Earlier descriptor/flags recovered (2026-09-27)
140ownedregiontable scan512records findsuniqueowner139893600 forentrant;source+46flags4352matchreference. Nativeextractionusesearlierowner/flags/material/palette,full32940bytesmatch. Laterargumentsonlyverification. Researchtargetidentitystillgiven;nextreusablecandidatecomponent withfailuretests/visibilityselection.

### Native candidate guards (2026-09-27)
nf_wall_owner:uniquevalidregionowner,10atomicfailure/boundschecks andcapturedregressionpass. nf_candidate_palette:usedindexagreementunlitonly,516checks inclall256conflicts/unusedchanges/bounds;captured140/141passes. Strictbuilds pass. Nextcomposeolder-ownedextractor;no livecandidatepolicyyet.

### Composed unlit candidate extractor (2026-09-27)
nf_extract_wall_candidate combinesowner/material/animation/usedpaletteguards withnativewall extraction;coherentreader/palettes callercontract. Earlier140plainreader yieldsfull32940byteexactrecord. Missingpalettes/misalignedsourceatomicrejectionpasses. Lit/hidden/extendedUVunsupported. NextcheckedbridgeAPI/lifetimetests thenvisibilityselection;no liveinsertionyet.

### Checked candidate bridge (2026-09-27)
nf_live_completed_wall_candidate tiesownedsource/palettes tofullsceneidentity/state;callerownsresult. Exactcapturedmatch pluswrongbounds/state/source,eviction/resetatomicrejections pass. Returnedcopyhashsurviveshistory/reset. Nextboundedselection/insertion;notlivevisibilitypolicyyet.

### Publication-time candidate replay (2026-09-27)
140sinkextractswallbefore141exists;buildernowreads140packetandownedcandidateonly. Rendersstill0difference0/.5,1790pixelsentry.75. Futureassetdependenceremoved;hardcodedresearchidentityremains. Nextboundedautomaticenumeration/validation,notlivepolicyyet.

### Bounded candidate discovery (2026-09-27)
140publicationenumerateswallsfrom3capturedroadregions,excludesdrawn/duplicates:18attempts13extractable5rejected. Knownentrantdiscoveredwithoutidentityselectioninput. Acceptednotvisible:dynamic hidden overrides/backface/frustum/occlusionstillneedchecks. No batchliveinsertion. Scopeunlitwallsinroadregionsonly.

### Hidden override precedence (2026-09-27)
Candidatevisibilitynowmatcheswall_draw_plan:overridehiddenbitreplaces sourcehiddenbit.9focusedchecks pass;18/13/5candidatecountsunchangedandcapture/lifetimeregressionspass. Doesnotestablishfrustum/backface/portalvisibility. Nextprojectcandidatebounds/sourcevisibilitybeforebatchinsertion.

### Candidate-set frustum audit (2026-09-27)
13candidatesx5poses:8overlapatsamples;7alreadyoverlapalpha0yetoriginallyundrawn.5nosampleoverlapnotcontinuousproof. Knownentrantonly.75/1. Bothsignedareapolaritiespresent. Cannotbatchinsertusingfrustumalone;recoverportal/backface/occlusiongatesnext. No livechange.

### Portal gate audit (2026-09-27)
140nativevisibility+regionreconstruct coversall13candidates,allflags0x1104(skip4). Sevenfullviewport-overlappingextrasbelongregion89portalX2..8,notfullscreen. Entrantregion87X2..47. Skip4alsoorientation/emptyspan,soindividualreasonneedsdetail. Nextcoherentinterpolatedportalposeevaluation;do notnaiveunion.


## 2026-09-27 continuation: checked retained camera input access

Bound completed surface snapshot clones to their verified scene identity before publication. Previously these clones were unbound, preventing checked pose evaluation even though their separate entry identity was valid. Added atomic checked snapshot pose readback plus research-bridge completed-scene pose/read-evaluate APIs, scoped to active epoch and exact serial/refresh bounds. These expose owned base/query/view inputs without changing simulation or enabling candidate insertion.

Research bridge build passed. The 850-refresh / 206-scene provenance regression passed (4,234 reads). For scenes 140 and 141, overriding with each scene's own retained inputs reproduced all 4,676 result bytes exactly. Eight wrong-identity cases rejected both operations without modifying outputs; eviction and state-reset checks also passed. Candidate extraction and lifetime checks remain passing. Retained query and builder rotations have opposite off-diagonal signs; translations are stored separately. Interpolating the 26 words blindly would not establish coherent camera inputs.

Next dependency: reconstruct mutually consistent base/query/view matrices at intermediate rigid camera poses, verify endpoint equality, then recompute portal bounds and candidate clipping across 140/141. No live extra-wall insertion or full-scene 60-fps gameplay claim. ROM, saves, ordinary bridge, stable fallback and original timing remain untouched.


## 2026-09-27 continuation: camera-to-portal matrix contract verified

Extended retained provenance regression to compare all 206 scene camera poses with their owned visibility inputs. Every scene has query rotation equal to the transpose of the retained view 3x3, zero query translation, view X/Z translation equal to negated arithmetic base>>8, and native camera position equal to negated view translation. Quaternion rotation must be compared against column-major view storage (the initial row-major comparison correctly exposed large sign differences). With the correct layout, maximum normalized coefficient error is 0.0000653123, below the regression bound 0.00007; original fixed-point matrix quantization is not exactly preserved by normalized quaternion recovery.

850-refresh regression passes, including new 206-scene relationship assertions and existing identity, palette, candidate and lifetime checks. This supplies a measured conversion contract for this route, not a universal camera-mode proof. No intermediate portal evaluation or live candidate insertion was enabled this run.

Next dependency: implement a guarded intermediate-pose adapter using this layout, retaining exact endpoint inputs and sub-unit base precision; evaluate portal records and entrant eligibility across 140/141. Avoid silently deriving exact original fixed-point endpoints from normalized quaternion coefficients. Full-scene 60-fps gameplay remains unverified. Stable fallback, ordinary bridge, ROM, saves and simulation timing untouched.


## 2026-09-27 continuation: intermediate portal camera adapter

Added visibility_pose.c / nf_visibility_pose_sample to the research bridge. It validates the measured planar camera contract, decodes column-major Q14 rotations through the shared rigid-pose sampler, reconstructs mutually transposed query/view rotations, and interpolates signed Q8 base coordinates before deriving view X/Z translation. Exact alpha 0/1 copies preserve captured quantization. Unsupported layout, non-finite/out-of-range alpha and invalid pointers fail without publishing output. This is explicitly a planar research adapter, not a universal camera-mode conversion.

Strict -Wall -Wextra -Werror compilation passed; research bridge build and 850-refresh / 206-scene regression passed. Seven samples across 140/141 evaluate successfully against the older owned snapshot. Both endpoint input copies are byte-exact; five invalid cases reject atomically. Region87 horizontal portal changes from 2..47 to 2..60; region89 changes 2..8 to 2..26, and acquires an additional queue record at alpha .9 (4..24), becoming 6..26 at 1. Root88 remains 0..238. This demonstrates actual intermediate visibility evaluation rather than freezing old portal bounds.

Next dependency: reconstruct wall edges with each sampled view matrix and apply per-record portal clipping/eligibility, including repeated region records, then compare candidate injection visually. The old retained state's matrix pointer must not silently supply the old view during region reconstruction. Exact endpoint input preservation is verified; cross-snapshot endpoint result equivalence and candidate visibility are not yet verified. No live renderer insertion or 60-fps gameplay claim. ROM, saves, ordinary bridge, stable fallback and simulation timing untouched.


## 2026-09-27 continuation: sampled wall portal eligibility

Extended boundary audit to reconstruct all candidate-containing queue records using an owned-reader overlay for the sampled 48-byte view matrix at state+0x54. Other reads remain checked against scene140. Repeated region records are retained separately with their viewport and queue index. Matrix override reads are counted and required; every reconstruction succeeds.

Seven samples pass: all 13 candidates have rejection bit4 through alpha .75; only source139937176 clears it at .9 and 1 (flags0x1100), under region87 bounds2..59 and2..60. Other12 remain rejected, including candidates in repeated region89 records. This narrows the known wall's admission transition to (.75,.9] for these samples, not an exact continuous threshold or final raster visibility proof.

An attempted full alpha0 flag comparison exposed stale auxiliary flags in the earlier portal audit, which read query-time RAM's matrix rather than the separately retained builder view. Correct override produces0x1124 for139937992 and0x110c for139937448 instead of0x1104; all still reject through bit4. Regression now checks the shared rejection outcome and records the corrected detailed flags, without claiming full flag equivalence. 850-refresh /206-scene regression passes with candidate-set admission assertions.

Next dependency: native checked region-at-pose API and wall draw-plan/vertical clipping verification, followed by bounded candidate replay insertion using each qualifying portal record. Clearing bit4 alone is not full material/vertical draw eligibility. No live insertion or full-scene60 gameplay claim; ROM, saves, ordinary bridge, fallback and timing untouched.


## 2026-09-27 continuation: checked native region-at-pose reconstruction

Added NFVisibilityRegionResult and nf_visibility_snapshot_region_at, exposed through nf_live_completed_region_at. The API verifies scene identity, reevaluates visibility at the supplied pose, selects an actual queue ordinal (preserving repeated region records), overlays the same sampled view for reconstruction, and publishes owned state/record/edges/stream only on success. It does not accept a caller-forged queue record. Ordinals outside evaluated count or20 fail; hidden/failed reconstruction leaves output unchanged.

Research bridge and strict snapshot compilation passed. 850-refresh /206-scene regression passes. All23 region samples match the diagnostic overlay byte-for-byte across the complete3472-byte result.69 invalid ordinal/boundary calls reject atomically. Existing13-candidate admission assertions remain passing. This is a native component API, not live candidate rendering.

Next dependency: use reconstructed edges/state with wall draw-plan and vertical clipping checks, then bounded candidate replay insertion using exact portal records. Per-call reevaluation is deliberately correctness-first; repeated requests should eventually share an immutable evaluated-scene object before performance-sensitive integration. ROM, saves, ordinary bridge, stable fallback and original timing untouched; full-scene60 gameplay unverified.


## 2026-09-27 continuation: sampled full wall draw-plan checks

Extended sampled region regression through nfs_visibility_wall_draw_plan using reconstructed state, owned source vertices and sampled edges. Runs first pass and any returned deferred mask, retaining queue ordinal and viewport for candidate results. This applies recovered hidden override, edge/deferred rejection, vertical rejection and animation/material selection rather than treating cleared bit4 as sufficient.

850-refresh /206-scene regression passes. Across seven samples, no candidate draw plans through alpha .75; at .9 and1 only139937176 is selected, first pass, material138327228, texture137744860,128x64, source flags0x1100. Texture address matches older retained candidate source. Other12 candidates remain excluded. Assertions cover exact candidate selection, pass, dimensions, texture and flags.23 native reconstruction comparisons and69 invalid request checks remain passing.

Next dependency: bounded replay candidate insertion with per-portal viewport clipping and shared sampled camera, then image comparison near the admission transition. Draw-plan acceptance does not establish correct high-resolution raster clipping or ordering. Deferred-plan code is exercised only when mask exists; this result does not claim comprehensive second-pass coverage. No live change; full-scene60 gameplay unverified. ROM, saves, ordinary bridge, fallback and timing untouched.


## 2026-09-27 continuation: portal-clipped candidate replay

Added portal_candidate_preview.c, a separate diagnostic depth-replay executable using the existing surface clipping hook. For the known candidate-140 packet (one appended unlit wall), only the last surface receives validated NF_CANDIDATE_PORTAL scissor bounds; missing/invalid bounds hide it. Other surfaces retain their ordinary rendering. Original-aspect 3240x2160 viewport uses pixel-center conversion from240x160 portal coordinates. This fixture-specific wrapper is not a general candidate policy and must not be used with arbitrary packets or at an endpoint selecting a different packet.

Built and rendered alpha .9 with checked draw-plan bounds2,59,0,158 and a matching hidden-candidate control. Difference is2957pixels, bounding box(327,1151)-(364,1232), entirely inside the portal. Inspected the cropped output: narrow textured wall strip appears at the left building edge, with no viewport-spanning geometry. Both runs24model faces,0lighting fallbacks. Report and crop archived; private replay packets unchanged.

Next dependency: automate multiple phases around admission, compare exact endpoint/control behavior, and replace fixture-last-surface assumption with validated identity/portal records before integration. Need determine pixel boundary convention against original clipping and assess motion continuity, not just containment. Single-frame diagnostic success is not smooth60 gameplay. ROM, saves, ordinary bridge, stable fallback and timing untouched.


## 2026-09-27 continuation: seven-phase portal replay regression

Added optional diagnostic packet-selection hook to packet_preview.c; ordinary builds compile it out. portal_candidate_preview now locates the known wall by its five-word identity in scene140 rather than assuming last surface. At scene141 exact endpoint it applies no candidate override, preserving captured geometry. This remains fixture-scoped by serial/identity, not a general lifetime/epoch policy.

Added reproducible test_portal_replay.py driving bounds from sampled native draw-plan report, comparing against ordinary diagnostic depth replay.14 renders across seven phases pass:0,.25,.5,.671377,.75 are pixel-identical to control; .9 adds2957pixels within portal bounds;1 is pixel-identical to the original newer scene. Exact endpoint therefore no longer clips/hides an unrelated last surface. Existing report supplies admission decisions; runner does not independently recompute them.

Next dependency: denser samples around(.75,.9), determine subpixel portal convention and remaining discontinuity at capture boundary, then generalize candidate metadata/identity scoping before live integration. Seven static comparisons are not continuous motion proof. Archived sources/test/report. ROM, saves, ordinary bridge, stable fallback and timing untouched; full-scene60 gameplay unverified.


## 2026-09-27 continuation: dense entry and endpoint measurements

Expanded sampled visibility/draw-plan regression to17 phases, with62 exact native region comparisons and186 atomic rejection checks, all passing. Candidate admission is absent at .76 and present at .78, narrowing the sampled threshold to(.76,.78]. Only the known wall is admitted thereafter.

34 diagnostic4K renders pass containment/control checks. Added patch grows from332pixels at .78 (4px-wide bounding strip) to5021pixels at .999999, all inside supplied portal. At exact1, output still matches original captured scene. However the .999999-to1 handoff changes136377pixels versus141398 in the control: candidate insertion removes5021 changed pixels but substantial remaining scene/material discontinuity persists. These whole-image counts include unrelated source changes and are not a pure wall-continuity metric. Do not claim the boundary is fixed.

Replay runner now records adjacent-image change counts. Replaced slow Python pixel loops with channel-maximum histogram counting; verified against a three-pixel mixed-channel fixture (same any-channel-nonzero semantics). Captured report was produced before this counting-only optimization. Next dependency: isolate remaining endpoint changes with fixed pose/material controls and determine whether the wall itself still differs due portal convention. Then generalize bounded candidate selection. No live integration; full-scene60 gameplay unverified. ROM, saves, ordinary bridge, stable fallback and timing untouched.


## 2026-09-27 continuation: controlled handoff isolates scissor mismatch

Added test_portal_handoff.py: builds a candidate scene140 variant with exact scene141 camera/object poses, holds shared world RGBA fixed using existing controlled-variant generator (one texture replaced), and compares near-end candidate with captured scene141. Portal-clipped candidate differs by2005pixels at(300,1152)-(327,1228). Full-viewport candidate control is pixel-identical to captured replay. Regression asserts both results; inspected three-panel crop confirms missing narrow left-edge strip.

This isolates a mismatch between our added portal scissor and the existing captured native replay representation. It does NOT establish that original GBA rasterizer ignores portal clipping: captured packets may retain full geometry without original clip state. Treat portal bounds as verified admission inputs; do not assume they are the final raster scissor. Prior136377pixel uncontrolled handoff includes shared texture changes; controlled result removes that confound and isolates2005pixels. No broad full-viewport candidate policy adopted.

Next dependency: recover original wall raster clip state versus region admission bounds and preserve it consistently for captured and inserted surfaces. Then choose a coherent diagnostic rendering policy and rerun entry/handoff comparisons. Native full-scene60 still unverified; stable fallback, ordinary bridge, ROM, saves and timing untouched. Archived test/report/crop; private packet variants remain under work.


## 2026-09-27 continuation: draw-time clipping bounds recovered

Added checked nf_live_completed_surface_bounds returning four owned draw-time state halfwords atE2..E8 by exact scene identity and draw ordinal. These come from retained per-draw overlay, not query-time RAM. Captured bounds for source139937176 scene141 ordinal4 are exactly[2,60,0,158], matching sampled region87. Regression asserts this and checks4234 wrong-boundary calls preserve output;850refresh/206scene tests pass.

Source inspection confirms nf_extract_wall serializes full world quad/UV/RGBA and lighting but not draw bounds; current replay therefore loses clip state. Existing native_wall horizontal reference converts coordinates/bounds to paired columns (left>>1,right rounding), and vertical reference has terminal-row behavior. Thus exact4K scissor edge convention still needs faithful treatment, but dropping clipping because full-viewport matches the old replay would reproduce missing metadata, not resolve correctness.

Next dependency: add separately owned per-surface clip metadata to diagnostic capture/replay and apply consistently to captured and inserted walls, preserving packet compatibility/stable builds. Validate paired-column/terminal-row semantics before generalizing4K convention. No live change; full-scene60 gameplay unverified. Archived bridge/test/report/VISIBILITY. ROM,saves,ordinarybridge,fallback,timing untouched.


## 2026-09-27 continuation: packet-bound clipping sidecars

Added clip_metadata.py version1 diagnostic JSON sidecar builder/validator. Records retain packet surface index, original draw ordinal, five-word identity and four draw-time bounds, bound to epoch/serial/refresh interval plus exact packet SHA256. Draw-order permutation is checked, preserving duplicate identities by index/ordinal. Existing NSP1 format unchanged. Capture validates206sidecars spanning4234draws; private paired packets/sidecars140/141 saved under work for replay.

850refresh regression passes.11 corrupt metadata mutations rejected (epoch/serial/bounds interval/hash/count/index/ordinal/identity/bounds encoding). During implementation, capture-local b/size names were found reused by older diagnostics; sidecar construction now rereads callback packet using header-declared packet size, preventing accidental pose-buffer serialization. Sidecars contain captured data only; they must not be reused unchanged for interpolated visibility or modified candidate packets.

Next dependency: load validated sidecars in the diagnostic renderer and combine captured per-surface clip bounds with sampled candidate records, including lighting scissor intersection. Bounds encoding is preserved as unsigned16 values; raster semantics and empty rectangles are intentionally not reinterpreted here. No live integration or60fpsclaim. ROM,saves,ordinarybridge,fallback,timing untouched.


## 2026-09-27 continuation: lighting scissor composition

Added preview_scissor.h and updated road_preview.h lighting runs to intersect column scissors with an existing surface clip instead of replacing it. Restores prior enabled state and rectangle after lit rendering. This closes a concrete integration hazard: earlier diagnostic surface clips were overridden by lit-wall columns. No existing binary fallback was rebuilt.

New offscreen GPU test checks1600pixels for exact rectangle intersection, disjoint zero-width intersection, enabled-state restoration and disabled-state restoration. Pass. Rebuilt diagnostic packet-depth-preview; scene204/205 replay renders19faces,2litwalls,0lightingfallback. That replay is a smoke test, not pixel-equivalence proof. Source now queries/restores scissor state per surface; performance impact is unmeasured and should be considered before live adoption.

Next dependency remains validated clip-sidecar consumption and consistent per-surface captured/candidate bounds, now with lighting composition supported. Paired-column raster semantics remain unresolved for4K. ROM,saves,ordinarybridge,stablefallback,timing untouched; full-scene60 gameplay unverified.


## 2026-09-27 continuation: captured wall sidecar consumer

Added render_captured_clips.py: verifies JSON sidecar exact packet hash/epoch/identity mapping and produces ordered bounded binary clip input for captured_clip_preview.c. Separate executable validates scene interval, surface count and every identity; accepts only exact acquired endpoints (alpha0), rejects trailing data. Applies captured bounds to walls only, with existing lighting-scissor intersection. Existing packet format and ordinary renderer binaries unaffected.

Scene141 renders24faces with0lightingfallback; inspected960x540 preview of4K output. Intermediate request exits31 and corrupted identity exits32. These are diagnostic gate tests, not original-raster pixel accuracy. Loader's SHA256 validation is in the launcher; native binary independently checks metadata identity but does not hash packet contents, so direct executable bypass is not equivalent to validated launcher. Pixel-center rectangle mapping remains provisional; no paired-column/terminal-row parity claim.

Next dependency: compare consistently clipped captured/candidate handoffs, then recover exact raster boundary semantics and expand beyond one fixture. Captured clipping must not be frozen across moving-camera samples. Archived source/launcher/report/preview; private clips/packets retained only under work. Full-scene60 gameplay unverified; ROM,saves,ordinarybridge,stablefallback,timing untouched.


## 2026-09-27 continuation: consistently clipped controlled handoff is exact

Added test_consistent_clips.py. Validates captured scene141 sidecar, maps its bounds by unique identity onto both controlled fixed-pose/shared-material packets (older includes previously extracted candidate), and generates explicitly labeled synthetic sidecars. Rejects duplicate identity ambiguity. Both render through captured clipping consumer at exact endpoints, avoiding any frozen-intermediate-pose claim.

Two4K renders compare pixel-identically:0changedpixels. Thus the prior2005pixel strip mismatch disappears when captured and inserted walls share clipping policy; no need to drop clipping to match the old unbounded replay. This is controlled endpoint evidence only. Original material animation differences and dynamic portal evolution are deliberately held out of the test; candidate live scheduling remains undone.

Next dependency: preserve per-record sampled clip metadata for all rendered walls during interpolation, including repeated region visits, then test original paired-column/vertical terminal-row conventions. Synthetic transferred bounds must stay confined to this fixed-pose diagnostic. Archived test/report/VISIBILITY; private synthetic sidecars and packets remain under work. ROM,saves,ordinarybridge,stablefallback,timing untouched; full-scene60 gameplay unverified.


## 2026-09-27 continuation: all queued wall-plan coverage audit

Expanded17sample reconstruction from candidate-containing regions to every queued region, preserving all wall plans with region/queue/pass/material/viewport.96native reconstruction comparisons and288atomic checks pass within850refresh regression. Plans increase8to11at .78, including repeated sources139938536 and139938604 under different region89 portal records; candidate139937176 still follows expected admission.

Endpoint coverage comparison exposes incompleteness: source139970292 with bounds[0,238,0,158] is captured in both scenes but absent from queue-derived plans. At1, two additional plans for139938536/139938604 under[6,26,0,158] are absent from captured draws. Do not discard repeats or replace captured scene with these plans yet. New test_wall_plan_coverage.py asserts these known gaps and emits coverage_complete=false, so test PASS cannot be confused with complete reconstruction.

Next dependency: trace missing wall's alternate draw path and region89 repeat suppression/merge behavior. Resolve these before publishing per-sample full-wall clip metadata or live integration. No new rendering policy enabled. ROM,saves,ordinarybridge,fallback,timing untouched; full-scene60 gameplay unverified. Archived capture/coverage tests/reports/VISIBILITY.


## 2026-09-27 continuation: merged queue suppression and missing-wall ownership

Queue builder nfs_visibility_merge marks subsequent visits with flag8 after expanding the first member's bounds. Sampled draw-plan audit now skips these already-merged records rather than treating them as independent draws. At endpoint1, region89 queue index5 flags9 is suppressed. This removes both extra wall plans; reconstructed counts are8at0 and9at1. Native region reconstruction remains a component API; caller applies queue eligibility.

Captured missing wall traced through owned surface arguments and bounded owner lookup: source139970292 belongs to descriptor139898112, region181, absent from sampled endpoint queue [88,87,289,89,238,89]. Base material118, flags8448(0x2100); resolved material138329820 at140 changes to138329852 at141. Thus it is not an unrecognized source within a queued region; alternate draw orchestration must be recovered. No assumption yet that it is safe to keep it globally visible.

850refresh regression passes,85native region comparisons and255atomic checks. Coverage regression now reports zeroextra endpoint plans but still one missingwall for both scenes (coverage_complete=false). Next dependency: trace region181 drawing entry/caller and its selection rule, retaining original material timing. Then publish full sampled wall coverage. ROM,saves,ordinarybridge,fallback,timing untouched; full-scene60 gameplay unverified.


## 2026-09-27 continuation: missing region's owned draw origin

Research bridge now retains six origin words per surface: region geometry entry LR, record pointer from entry stack, and copied16-byte record. Exposed checked scene/ordinal origin API; capture records it for missing wall. Both140/141 yield LR03002964, record03007DC8, halfwords[181,0,238,0,158,0,0,65535]. Region record is stack-resident, outside retained visibility queue.

Read-only ARM disassembly around03002960 confirms generic region draw calls03001800 after placing r6(record pointer) on stack, returning03002964. This establishes concrete draw provenance but does not yet identify who synthesized/selected181; do not infer global visibility.850refresh regression passes, including existing surface/candidate/sidecar checks. Origin copy uses currently retained region event, intended for these wall diagnostics; no broader road provenance claim.

Next dependency: capture caller/entry arguments at0300264C for stack-backed records, trace synthetic region selection and reconstruct its lifetime rule. Then incorporate this additional path in sampled scene coverage. ROM,saves,ordinarybridge,fallback,timing untouched; full-scene60 gameplay unverified. Archived bridge/capture/report/VISIBILITY.


## 2026-09-27 continuation: missing wall is object-selected region draw

Expanded research origin record from6to12words with030027F0 entry LR/SP/r0-r3. Both missing-wall captures return to03002364 with state030000C0 and stack record03007DC8. Read-only ARM trace03002320..2360 selects this path when object flags bit0x10 is set, reads region from object+0x36, copies current bounds, then calls region draw. This matches existing nfs_visibility_object_region helper, not a new global-region policy.

850refresh regression passes; missing-wall caller assertions pass and existing object-region differential stats are [194, 194, 0, 191, 0, 0, 0] (field2 mismatch count0). Origin API changed to12words, and its sole diagnostic caller was updated. The queue-only coverage gap is therefore missing object-dispatch integration, not unexplained visibility. Existing helper requires draw-time object/state inputs; blindly enumerating all flag0x10 objects would bypass collection/visibility rules.

Next dependency: retain object-selected region events with parent identity and owned object/current bounds, then include their native reconstructed records in sampled wall coverage at the proper object-dispatch position. Preserve original animation selection timing. ROM,saves,ordinarybridge,fallback,timing untouched; full-scene60 gameplay unverified.


## 2026-09-27 continuation: owned object-selected region inputs

Research surface records now own object address and164-byte draw-time object capture for direct03002364-selected region calls. nf_live_completed_object_region checks epoch/scene/bounds/ordinal, rebuilds16-byte region record with native helper and retained per-draw state, compares it against captured origin, and atomically returns184bytes(address/object/record). No live RAM read at consumption.

850refresh regression passes. Missing wall140/141 both reconstruct exactly and reference region181; wrong-boundary requests leave payload unchanged. Existing194object-region differential checks remain passing. This direct-call association is not a general nested-object-region stack implementation; unrecognized/nested cases must not be assumed covered. Per-draw memory increases164bytes plus address in research capture.

Next dependency: reconstruct these owned object-selected records at sampled camera while preserving parent draw bounds/order and material timing, then combine with queue plans and verify endpoint coverage. Object dispatch eligibility must be retained/recomputed, not all flag0x10 objects globally emitted. ROM,saves,ordinarybridge,fallback,timing untouched; full-scene60 gameplay unverified. Archived bridge/test/report/VISIBILITY.


## 2026-09-27 continuation: retained object path closes endpoint wall coverage

Sample audit now reconstructs the owned scene140 object-selected region record alongside eligible queue records at17poses. Records carry original object dispatch ordinal separately; appended diagnostic plan order is not claimed to reproduce original command ordering. Native geometry/draw-plan uses sampled matrix with older retained assets. Object event remains retained eligibility/current bounds, not recomputed object collection.

850refresh regression passes with17object-region reconstructions. Endpoint wall source/bounds multisets now exactly match captured draws, including multiplicities:9draws at140 and10at141, no missing/extra entries. Coverage report marks endpoint_wall_identity_bounds_complete=true and interpolated_dispatch_verified=false. This does not verify endpoint material timing: known object's animated material changes at141 while reconstruction uses140assets.

Next dependency: carry complete sampled wall clip plans into diagnostic replay with object dispatch ordering preserved; separately validate object collection/eligibility across poses and original animation updates. No claim of complete scene snapshots or60fpsgameplay. ROM,saves,ordinarybridge,fallback,timing untouched. Archived capture/coverage tests/reports/VISIBILITY.


## 2026-09-27 continuation: all-wall sampled clipping replay

Added NF_SAMPLED_CLIPS research build of captured clip consumer: binary clip input includes expected alpha, checked against acquired timeline within1e-9; existing exact-capture mode remains separate. render_sampled_clips.py maps unique sampled wall sources to augmented packet identities, rejects missing/duplicate mappings, hides unselected walls, and retains original packet command order. Candidate remains appended as in fixture; this does not establish ideal draw position. Roads are unchanged.

Rendered16intermediate4K samples successfully from0through.999999; source packet hash logged. A .9 clipping file with .8 render request exits34. Inspected four-frame montage around.75/.78/.9/.999999. This demonstrates using refreshed clips for all walls rather than frozen captured bounds. Exact1 deliberately uses captured sidecar path, not this sampled metadata. Object event eligibility/bounds still retained from140; no independent sampled object collector proof.

Next dependency: quantitatively compare sampled-to-captured handoff under consistent material timing, verify candidate/order and object dispatch behavior, then move bounded clip plan production into native scene ownership before live integration. Pixel-center raster convention remains provisional. ROM,saves,ordinarybridge,fallback,timing untouched; full-scene60 gameplay unverified. Archived sources/report/preview/VISIBILITY.


## 2026-09-27 continuation: sampled handoff differences isolated

Added test_sampled_handoff.py comparing all-wall sampled.999999 to exact captured141 with consistent clipping. Raw difference134372pixels. Holding shared world RGBA fixed leaves33pixels; material-only control changes134339pixels in(1075,0)-(1436,804). With exact endpoint camera/object poses as well as shared RGBA fixed, sampled replay matches captured control exactly:0pixels. Regression asserts these controlled results.

This closes the tested geometry/clip handoff mismatch for this fixture: remaining large visible change is captured texture animation/material update, not missing wall geometry.33near-end pixels disappear with exact poses, consistent with tiny interpolation/raster differences. Do not smooth away animation updates or alter original simulation timing; original material scheduling remains authoritative. Candidate appended order happens to match this depth-rendered fixture under controls, not a general ordering proof.

Next dependency: implement bounded native sampled wall-plan ownership with exact scene/pose identity and original material boundaries, then test broader scene/object eligibility before live renderer integration. Current output still offscreen diagnostic; no playable native60claim. ROM,saves,ordinarybridge,fallback,timing untouched. Archived newtest/report/VISIBILITY.


## 2026-09-27 continuation: native owned queue-wall plans

Added NFSampledWallPlan fixed2068-byte value output (record plus up to64 source/pass/draw entries) and checked snapshot/bridge wall-plan APIs. Reconstructs queue region at supplied pose using owned state, preserves source addresses/material selection/pass, suppresses merged flag8 records, and publishes only after success. No borrowed pointers. Object-selected regions remain separate; not full scene API.

Research build and strict snapshot compilation pass.850refresh regression compares85native plans against diagnostic draw-plan compositions, including every source/pass/edge/material/texture/dimension/flag and record; all exact. Invalid ordinal preserves output. Existing region/sidecar/object tests pass. Merged-empty behavior implemented but not separately exercised through newAPI by this test (audit skips merged inputs).

Next dependency: add merged/epoch/lifetime API coverage and object-selected plan path, aggregate bounded scene plans without repeating evaluation per region, then connect to diagnostic/live consumer. Original materials come from owning snapshot; no animation retiming. ROM,saves,ordinarybridge,fallback,timing untouched; full-scene60 gameplay unverified. Archived source/headers/bridge/test/report/VISIBILITY.


## 2026-09-27 continuation: native wall-plan lifetime/merged verification

Expanded new native API regression:11merged flag8 queue records return success with original record, count0 and fully zeroed unused draw storage.340wrong epoch/serial/begin/end requests reject atomically across85successful plans; null-pose requests and invalid ordinals preserve output. Evicted-scene and reset-epoch calls also reject unchanged. All85caller-owned plan buffers retain hashes after eviction and reset.

850refresh/206scene regression passes. This verifies the new output ownership and rejection contract before broader integration, not additional rendering capability. No source renderer changes this run.

Next dependency: extend native owned plan production to retained object-selected region events, then aggregate scene plans under one sampled evaluation and preserve dispatch order/material boundaries. ROM,saves,ordinarybridge,fallback,timing untouched; full-scene60 gameplay unverified. Archived expandedtest/report/VISIBILITY.


## 2026-09-27 continuation: native object-selected wall plans

Refactored shared reconstructed-region wall planning and added snapshot_object_plan plus checked completed_object_wall_plan bridge. Bridge obtains owned draw state/object by validated scene and draw ordinal, requires direct object-selected origin, reconstructs record with native helper and geometry with sampled view, then produces same bounded owned plan as queue path. Snapshot helper explicitly requires coherent caller-owned state/object; bridge provides that contract. Object eligibility remains retained, not recomputed.

Research build and strict snapshot compilation pass.850refresh regression:17native object-wall plans exactly match diagnostic source/pass/material/geometry-selection records,85queue plans still exact,408identity rejection cases atomic.11merged-empty and retained-output lifetime checks still pass. One common test block currently shares queue invalid-ordinal check even for object case; object-specific out-of-range coverage still to add.

Next dependency: aggregate queue/object plans into owned scene-level output without repeated evaluation, preserving dispatch ordering, then connect bounded renderer consumption and broaden object eligibility validation. Material animation stays at original capture boundaries. ROM,saves,ordinarybridge,fallback,timing untouched; full-scene60 gameplay unverified. Archived snapshot/source/bridge/test/report/VISIBILITY.


## 2026-09-27 continuation: single-evaluation queue plan batch

Added NFSampledQueuePlans (41364-byte owned value, up to20queue records) and checked snapshot/bridge batch APIs. Evaluates visibility once, reconstructs each eligible region, preserves queue index and merged-empty records, zeroes unused slots, and publishes atomically after all succeed. Temporary result uses bounded heap allocation; failure frees it without output mutation. Object-selected plans remain separate pending dispatch assembly.

Research build/strict compilation pass.17batch outputs match all individual plans byte-for-byte, including11merged records and unused storage; wrong epoch rejects unchanged.850refresh regression passes. Corrected object-plan invalid-ordinal test to call the actual selected queue/object API with999, closing the prior test limitation. No performance claim yet; per-batch allocation and reconstruction costs unmeasured.

Next dependency: retain object-event dispatch placement relative to queued/model draws and assemble complete ordered native plan output, then renderer consumption and broader scene validation. Original animation timing unchanged. ROM,saves,ordinarybridge,fallback untouched; full-scene60 gameplay unverified. Archived source/headers/bridge/test/report/VISIBILITY.


## 2026-09-27 continuation: retained command dispatch provenance

Added checked completed_dispatch API returning bounded owned six-word command records:road/wall/model kind, original draw ordinal, source, direct object address, region descriptor, object-selected marker. Includes model marker at captured slot. Capacity validated before publication; insufficient capacity preserves output/count. This is captured ordering metadata, not an interpolated ordering algorithm.

850refresh regression matches all206command sequences to packet identities/model placement, with206capacity rejection checks.189emitted object-selected wall commands observed:165before model and24after. Critical boundary: source139970292/object33576028 is command11 before model12 in140, but command13 after model12 in141. Thus globally appending/prepending object plans is incorrect even for this fixture; depth-render control had masked ordering differences.

Next dependency: assemble sampled wall plans against retained command positions, define material/order boundary handoff consistent with original timing, and handle new candidate insertion explicitly.189emitted wall commands need not equal194object-region invocations (some calls emit no retained wall); no lost-event conclusion from counts alone. ROM,saves,ordinarybridge,fallback,timing untouched; full-scene60 gameplay unverified. Archived bridge/test/report/VISIBILITY.

## 2026-09-27 continuation: diagnostic ordered wall-plan assembly

Retained full six-word dispatch sequences in provenance reports and added ordered_wall_plans.py. Matches sampled walls to captured source/object-selected slots, retains road/model commands and relative order, omits unselected walls, and reports unmatched entrants separately. Rejects ambiguous repeated sources, duplicate plan assignments and missing model markers. Inputs remain unchanged. This deliberately conservative Python diagnostic is not integrated into the native consumer; complete means no pending insertion only, not full-scene correctness.

850-refresh provenance regression passes across206scenes/4234draws. New17sample ordering test passes with3invalid-input checks. Both exact endpoints reproduce every captured command; object wall139970292 remains before the model in140 and after it in141. Candidate139937176 is explicitly pending insertion for the10intermediate samples from.78 through.999999. Retaining old ordering between endpoints is a diagnostic policy, not proof of continuous object eligibility or correct intermediate ordering.

Next dependency: recover and validate candidate insertion from region/edge traversal relative to model/object dispatch, then implement native ordered consumption. No rendering/performance or playable milestone claimed. ROM,saves,ordinary bridge,stable fallback and original timing untouched. Archived helper/test/provenance source and reports.

## 2026-09-27 continuation: anchored first-pass candidate insertion

Added conservative assemble_anchored diagnostic. Recovered native_visibility.c wall plan loop traverses increasing edge/source addresses within each pass. Candidate139937176 therefore precedes retained139937244 in region87. Requires same queue record, contiguous retained region walls, first pass only, increasing unique source order, one descriptor and a later retained anchor. Unanchored, deferred or object entrants remain pending; does not infer entire region/model order.

17sample tests pass:10intermediate entrant insertions now reproduce captured141 world kind/source sequence, while every original command remains in its retained relative position. Exact endpoints unchanged. Three unsupported cases (deferred pass, unknown region, no later source anchor) remain pending. Original17sample ordering/rejection regression also passes. Endpoint world sequence comparison is independent captured evidence for this fixture, not general proof of intermediate painter order. Object/model order still retained from140 until141; road visibility unchanged. Python diagnostic not yet wired into rendering/native consumer.

Next dependency: consume this ordered diagnostic in sampled replay and verify clipping/material handoff, then extend ordering provenance to deferred passes and object/model dispatch before native integration. ROM,saves,fallback,ordinary bridge and simulation timing untouched; full-scene60 gameplay unverified. Archived helper/tests/reports.

## 2026-09-27 continuation: ordered sampled replay consumption

Added render_ordered_clips.py to consume assemble_anchored plans into private packet order sections. Resolves command kind/source to unique packet surfaces, preserves model marker and retained object placement, inserts admitted candidate at its region anchor, checks full permutation and asserts every byte outside order payload unchanged. Source packets untouched. Packet format requires all surfaces: nonselected walls remain at trailing positions with empty sampled scissors, explicitly checked against selected plans.

16offscreen3840x2160 sampled renders pass and are pixel-identical to previous appended-candidate depth replay. Structural order now follows recovered region traversal even though depth rendering masked prior order difference. Checks validate packet layout, unique identities, selected coverage, unchanged geometry/material/pose bytes and output equality. Source/output packet hashes recorded in ordered-clip-tests.json. No native live consumer or frame-rate claim; intermediate object/model ordering still retained rather than recomputed. Exact newer endpoint remains its captured replay path.

Next dependency: broaden dispatch provenance for deferred wall passes and object/model ordering, then port bounded assembly into native consumer. Clipping convention and broader scenes still need validation. ROM,saves,ordinary bridge,stable synchronized fallback and game timing untouched. Archived renderer script/report; large private packet and PPM fixtures stay under work.

## 2026-09-27 continuation: broader region-run provenance audit

Provenance capture now retains12-word origin for every nonmodel command across206scenes.850-refresh regression passes. Added dispatch-run audit:3176walls form1652contiguous region/object runs, each strictly ascending source order.86region reentries include85same-record wall-road-wall returns and one different-record revisit in scene53.80reentries descend in source address. Initial assumption that all86were same-record road-only returns failed; the test now records and checks the actual85/1split.

This rules out globally sorting region walls by source. Existing anchored insertion remains limited to contiguous same-queue first-pass peers and is not generalized. All3176wall geometry origins share03002964, so this caller alone cannot distinguish deferred-pass masks. New report preserves all reentry examples; no unsupported inference that the different-record revisit is a deferred pass.

Next dependency: capture explicit first/deferred pass boundary or mask at the region wrapper, validate against85same-record returns, and preserve different-record scene53 traversal separately before native assembly. No playable or60fps claim. ROM,saves,fallback,ordinary bridge and timing unchanged. Archived provenance source/report and run audit source/report.

## 2026-09-27 continuation: explicit wall-pass capture

Read original ARM wrapper:03002978 calls wall routine with first-pass mask;03002B34 calls it with deferred mask after roads/nested region work. Research bridge now retains wall-entry LR,input mask,record pointer per draw, exposed through exact-scene wall-only API. Existing12word origin API unchanged. Roads rejected; wrong scene boundary rejected without output mutation.

Research bridge rebuild and850-refresh regression pass.3176wall reads plus3176wrong-boundary and1058road rejection checks pass. Dispatch audit verifies2910first draws (return0300297C,mask0) and266deferred draws (return03002B38,nonzero mask). All85same-record reentries switch first to deferred; scene53different-record revisit is first to first. This closes pass-classification ambiguity without inferring passes from source order. Direct pass entry overwrites its own metadata even after nested region traversal; broader object provenance nesting remains a separate limitation.

Next dependency: attach explicit pass classification to ordered native plans, preserving deferred placement around road/nested/model commands; expand reconstruction beyond140/141 before live integration. No playable/60fps claim. ROM,saves,ordinary bridge,fallback and original timing untouched. Archived bridge,test sources,reports,VISIBILITY.

## 2026-09-27 continuation: pass-aware diagnostic assembly guards

Ordered assembly accepts explicit captured pass metadata, validates count/nonwall entries/known LR-mask pairs and rejects a sampled wall changing its captured pass. Ordered replay now supplies this metadata. Legacy diagnostic callers may omit it; native production use is not implied. Pass migration deliberately rejects instead of guessing a new placement.

205unambiguous captured sequences roundtrip exactly; one repeated-source sequence rejects as ambiguous.3164mutated wall-pass assignments all reject.17native sampled plan sets pass with metadata.16ordered4K replay renders remain pixel-identical. Broad205sequence test uses plans derived from capture, testing assembly/guards only, not independent native reconstruction. The one ambiguous scene remains unsupported by source-only matching and needs record/occurrence identity.

Next dependency: retain occurrence identity for repeated source draws (scene53), then broaden native reconstruction to deferred-pass scenes before C consumer integration. ROM,saves,ordinarybridge,fallback,timing untouched; no playable/full-scene60claim. Archived helper,renderer,test/report and refreshed replay report.

## 2026-09-27 continuation: scene-local occurrence assembly

Added explicit occurrence mode to diagnostic assembly. Every plan supplies captured command index; validates wall slot, source, object-selected class and optional pass metadata before routing. Duplicate assignments reject. Default source-only mode remains conservative and rejects ambiguous sources. Occurrence indices are local to a retained scene, not persistent cross-scene identity; caller must bind input collections to same scene.

All206captured sequences now roundtrip in occurrence mode, including repeated wall draws in53. Removing one repeated occurrence preserves the other and all remaining command positions. Six malformed/duplicate occurrence tests reject. Existing205source-only sequence and3164pass-mutation regression passes;17native sampled sets remain valid. These are assembly tests with captured plans, not expanded independent reconstruction.

Next dependency: broaden native sampled reconstruction to a deferred/repeated scene and derive occurrence mapping from retained region invocation data; do not use raw index across scene boundaries. Native consumer/live integration remains unfinished. ROM,saves,fallback,ordinary bridge,timing untouched; no full-scene60claim. Archived helper,tests,reports,VISIBILITY.

## 2026-09-27 continuation: repeated-scene native reconstruction

Extended850refresh capture to independently evaluate native queue plans at retained scene53pose. All11queue wall draws match captured source/pass multiplicities, including four sources each drawn twice and one deferred wall. New test maps each plan uniquely by full16byte region record plus source/pass to captured occurrence, then assembles exact captured order. No unmatched or extra queue plans. Object-selected draw remains capture-derived in this test.

Research provenance regression and repeated-scene mapping test pass. This improves upon prior capture-derived roundtrip: queue geometry/visibility/material-plan generation is now native for the repeated fixture, while occurrence placement is verified against captured metadata. Exact-pose only; record equality is not established as persistent identity across motion. Native plan material/geometry words retained in fixture but this test asserts source/pass/record and order, not rendered texture equality.

Next dependency: broaden exact-pose native queue coverage across deferred scenes and verify sampled record correspondence before native consumer integration. ROM,saves,fallback,ordinary bridge,timing untouched; no playable/full-scene60claim. Archived source,reports and compact reconstructed fixture.

## 2026-09-27 continuation: route-wide queue reconstruction and deferred mask fix

Broadened independent native queue reconstruction to all206retained poses. Found21scenes with extra deferred draws and no missing draws. Original ARM region wrapper03002980 ANDs returned mask with0xFF; snapshot wrapper retained all32bits. Fixed snapshot_region_wall_plan to apply the same low-byte truncation. Low-level wall-plan routine remains unchanged because the truncation belongs to its caller.

Research rebuild and850refresh regression pass after correction. All2987queue wall draws across206scenes now exactly match captured source/pass/full16byte-record multiplicities with no extras/missing, including repeated scene53. Coverage equality is now a persistent assertion in capture test; report records totals. Existing17sample and ownership/atomic checks pass. This was a real overdraw bug uncovered by broader fixtures, not a visual matching workaround.

Next dependency: verify captured material/geometry selection for these broad plans and sampled occurrence continuity before native ordered consumer integration. Object eligibility and live60remain unverified. ROM,saves,ordinarybridge,stablefallback and simulation timing untouched. Archived snapshot source,capturetest/report,routecoverage report,VISIBILITY.

## 2026-09-27 continuation: broad wall material-plan verification

Extended native plan checks beyond source/pass/record counts. All2987queue draws map uniquely by full region record/source/pass, and native selected material address,source flags,texture pointer,width,height match retained original draw inputs. Also independently reconstructs object-selected plans at each of189captured object wall draws and checks its matching source/pass/record and same material/texture fields. Uses retained draw-time object state, not query-time stale object bytes.

850refresh regression passes:2987native queue material matches plus189native object material matches, totaling3176walls across206scenes. Queue plans fully consumed; object check verifies each captured wall is present but does not yet assert absence of additional object-plan outputs or recompute object eligibility. Texture selection/dimensions equality is not full pixel/geometry or motion proof. Existing sampled and atomic checks pass.

Next dependency: complete object-plan multiplicity checks grouped by invocation, then sampled record/occurrence correspondence and native ordered consumer. ROM,saves,fallback,ordinarybridge,game timing untouched; no playable60claim. Archived updated capture test/report,VISIBILITY.

## 2026-09-27 continuation: emitted object-plan completeness

Added completeness check for each emitted object/descriptor/full-record group. All189native object plans contain exactly their captured wall with no extra output; all2987queue plans remain exact. Initial single-object-wall-per-scene assumption failed at144, which emits two different objects. Replaced with validated unique object/descriptor/record keys; each such group has one emitted wall in this route. Repeated identical groups deliberately fail pending explicit invocation identity.

850refresh regression passes with189object-plan-complete assertions. Together with queue coverage/material checks this covers3176emitted wall plans at captured poses. Does not cover zero-emission object invocations, recompute eligibility, or prove a general grouping algorithm; original194invocation versus189emitted draw distinction remains. No new renderer/performance claim.

Next dependency: explicit invocation identity/zero-output capture and native ordered consumer; sampled occurrence continuity still required for60fps full scene. ROM,saves,fallback,ordinarybridge,timing untouched. Archived updated test/report,VISIBILITY.

## 2026-09-27 continuation: native occurrence-order component

Added ordered_dispatch.c/h: bounded native scene-local selection (257commands/256walls), validates command kinds/pass LR-mask metadata, one model marker, occurrence/source/objectclass/pass and duplicate assignment. Returns owned ordered command indices, retains roads/model, omits unselected walls, zeroes unused slots, publishes only after full validation. No heap allocation. Caller must bind arrays to same retained scene; candidate insertion and cross-scene identity are deliberately outside this API.

Strict-O2-Wall-Wextra-Werror shared build passes.206captured sequences reproduce exact order; removing one wall preserves all other occurrence positions, including repeated scene53.1030invalid occurrence/source/pass/objectclass/duplicate tests reject with output bytes unchanged. Native component tests only, not live renderer integration or full-scene reconstruction. Research DLL separate; ordinary bridge/fallback not rebuilt.

Next dependency: connect checked completed-scene ownership to this C component, then integrate ordered packet consumption and sampled entrants. Object zero-output invocations and interpolated occurrence continuity remain unresolved. ROM,saves,timing untouched; no playable60claim. Archived C/header,test/report,VISIBILITY.

## 2026-09-27 continuation: completed-scene native ordering bridge

Added nf_live_completed_ordered_dispatch, resolving command/pass inputs from exact retained epoch/serial/begin/end before native selection. Caller supplies scene-local occurrence selections; stale/mismatched scene requests fail before output publication. Output is an owned index value. Research build links ordered_dispatch.c; normal bridge/fallback untouched. This binds captured command metadata, not proof that caller selections originated from that scene when identical fields happen to coincide.

Research rebuild and850refresh regression pass:206exact native owned-order results,824wrong-identity requests leave output unchanged. Existing3176wall material/completeness checks and sampled/lifetime tests pass. Renderer consumption, candidate insertion and independent scheduling remain separate work.

Next dependency: feed native reconstructed plan selections into this checked bridge and consume output in diagnostic renderer; then integrate live scene scheduling after occurrence continuity validation. Zero-output object invocation capture remains open. ROM,saves,timing unchanged; no playable60claim. Archived bridge/buildscript/test/report,VISIBILITY.

## 2026-09-27 continuation: reconstructed plans through owned native ordering

Capture now feeds selections from independent native queue/object plans into completed-scene native ordering. Python maps source/pass/full-record occurrences to retained command slots; native bridge resolves original commands/pass metadata and validates selection. Returned indices retained in report. Removed one reconstructed wall in a second call per scene to verify roads/model and remaining occurrence positions survive filtering.

850refresh regression passes:206reconstructed native order matches and206omission checks, alongside3176wall material checks and824scene-identity atomic checks. This joins native planning and ordering through a diagnostic adapter; occurrence mapping remains Python and exact-pose/capture-based. Renderer does not yet directly consume bridge result; candidate ordering path still separate.

Next dependency: move verified occurrence mapping into bounded owned C API and consume result in renderer. Cross-scene matching, zero-output objects and fullscene60timing remain unverified. ROM,saves,fallback,ordinarybridge,timing untouched. Archived capture test/report,VISIBILITY.

## 2026-09-27 continuation: fully native retained-pose occurrence mapping

Added completed_reconstructed_order: resolves owned exact scene, obtains retained pose, builds native queue plans, reconstructs object plans, uniquely matches source/pass/fullrecord to captured occurrences, checks material/flags and complete queue consumption, then returns native ordered indices. Bounded queue temporary freed on all exits; output publishes only via final checked ordering. Repeated identical object groups and multiwall object plans reject pending invocation identity support. Caller provides no selection arrays or Python occurrence mapping.

Research rebuild/850refresh regression pass:206all-native reconstructed orders byte-match independent diagnostic results including zeroed unused output,824wrong-scene/epoch/bounds requests leave result unchanged. Existing full wall coverage/material and sampled checks pass. This is exact retained-pose ordering component; it retains captured road/model placement and eligibility and does not generate a render packet or new intermediate ordering.

Next dependency: consume this owned native output in diagnostic renderer, then extend sampled mapping/candidate insertion with explicit invocation identity. Performance of added reconstruction/allocation unmeasured. ROM,saves,ordinarybridge,fallback,timing unchanged; no playable60claim. Archived bridge/test/report,VISIBILITY.

## 2026-09-27 continuation: native order output consumed by GPU replay

Capture writes owned reconstructed command indices for140/141 to private diagnostic sidecars. NF_NATIVE_ORDER preview variant validates scene interval,count,index permutation and EOF, translates native indices into packet surface/model commands and supplies an owned order buffer to existing GPU consumer. Source packet unchanged. File-mediated handoff only; not live bridge call from renderer. Exact full permutation only, no filtered packet/candidate path.

Research capture206scenes passes. New native-order-preview build renders141at3840x2160 pixel-identical to captured clipping baseline (0changed). Wrong scene,duplicate index,trailing bytes reject with35/36/37. Launcher validates packet clip JSON binding; native order binary carries interval identity but not epoch/hash, so reusable production sidecar binding still required. Test report stores packet/order hashes.

Next dependency: replace diagnostic file transport with owned in-process scene/order handoff and validate fullscene motion before live integration. Candidate insertion and zero-output object coverage remain open. ROM,saves,ordinarybridge,fallback,timing untouched; no playable60claim. Archived preview source,test/capture sources,reports,VISIBILITY; private sidecars/PPMs stay work.

## 2026-09-30 resumed: owned ordered render packet

User resumed work and continuation; existing heartbeat set ACTIVE, no duplicate created. Added completed_ordered_packet native API: validates packet structure, resolves exact owned scene/epoch, reconstructs native order, checks captured command kinds/sources against packet order identities, then builds independent owned packet with selected order section. Atomic output arguments; release via scene_packet_free. Geometry/material payload is caller-supplied and copied, not independently regenerated or cryptographically bound by this API; valid caller scene coherence remains required.

Research build and850refresh regression pass.206owned output packets byte-identical to captured packets at exact poses;206wrong-epoch calls reject unchanged output arguments. Existing native mapping/material/coverage checks pass. Exported owned140/141packets render at4K via normal captured-clip consumer without order sidecar,0pixel difference. Native sidecar negative checks still pass. Export remains a diagnostic test transport; live renderer has not yet called this API in-process. No performance/60fps claim.

Next dependency: connect owned-packet API to live snapshot publication with explicit lifetime/latency checks, then sampled candidate/occurrence ordering and zero-output object coverage. ROM,saves,ordinary bridge,stable fallback and game timing untouched. Archived bridge,test sources/reports,VISIBILITY. Completion not reached; continuation active.

## 2026-09-30 continuation: in-process ordered snapshot publication

Added completed_publish_ordered sink adapter: builds checked owned ordered packet, copies it into caller's single-owner snapshot store, then frees temporary packet on success or failure. Does not change global sink registration or stable renderer. Capture test calls adapter directly inside actual completed scene callback, acquiring the published scene afterward.

Research rebuild/850refresh regression pass:206publications exact in epoch/serial/time and packet bytes after temporary allocation freed.206attempts to republish while acquired reject and pinned bytes remain unchanged. Added store cleanup to test finally path. Store publication now in-process, but GPU consumer/live host is not yet connected and reconstruction latency unmeasured. No independent scheduling or fullscene60claim.

Next dependency: measure callback publication cost and wire research GPU consumer to same acquired store without changing original game timing; sampled insertion/occurrence and zero-output object coverage remain. ROM,saves,ordinarybridge,fallback untouched. Archived bridge/test/report,VISIBILITY.

## 2026-09-30 continuation: research GPU consumer receives ordered publications

Added --ordered opt-in to live_preview, resolving native publication adapter and passing the same single-owner snapshot store used by GPU acquisition. Measures native reconstruction/publication cost in existing rebuild column. Existing default/retained paths preserved; built separate live-ordered-preview.exe with diagnostic depth. This connects callback/store/GPU in-process, not a standalone native game.

Unpaced360refresh reload diagnostic succeeds:96packets,0publication failures,342rendered frames,1context,0lighting fallback,1stale-epoch suppression after reload. Route206publication regression passes with median0.44405ms,p950.8368ms,max0.939ms; separate live run median0.42295ms,p950.4953ms,max1.4566ms. These are observed publication costs, not end-to-end frame rate. New live consumer does not yet include sampled wall clipping/entrant insertion; existing rigid motion/depth behavior remains diagnostic. No60fpsgameplay claim.

Next dependency: carry wall clipping and sampled visibility/entrant metadata into the in-process consumer, then paced fullscene/timing/controller validation. Zero-output object invocation coverage remains. ROM,saves,ordinarybridge,stablefallback unchanged. Archived live source,capturetest/reports,CSV,VISIBILITY; output image/private fixtures remain work.

## 2026-09-30 continuation: retained clipping in in-process preview

Added opt-in --ordered-clips research preview. Scene callback copies draw-time bounds by packet surface index into16entry scene-tagged ring, clears ring on epoch change; acquired packet selects matching serial/begin/end metadata. Wall draw hook applies existing provisional GBA-to4K scissor convention and disables after draw; roads keep existing behavior. Bounds are owned, not pointers into expired bridge history. Missing metadata exits explicitly. Existing default/ordered paths keep clipping disabled.

Separate diagnostic-depth build and360refresh reload run pass:96packets,0failures,342rendered,0lighting fallback,1stale suppression. Captured bounds now reach live GPU path without files. These bounds belong to older retained pose; they are NOT recomputed at interpolated camera pose and may cause entry/clipping artifacts between snapshots.16slot metadata ring assumes single-owner same publication cadence as snapshot store; broader capacity/failure alignment still needs testing. Clip capture precedes publication, so failed publication may retain unused metadata but does not publish a scene.

Next dependency: sampled visibility/clip recomputation from retained pose/scene inputs and candidate insertion; test boundary images against established offscreen control before paced validation. ROM,saves,ordinary bridge,fallback,timing untouched. No playable60claim. Archived live source,CSV,VISIBILITY.

## 2026-09-30 continuation: live/offscreen clipping parity

Added optional NF_LIVE_CLIP_EXPORT diagnostic export while final snapshot pair is pinned, copying both packets and matching owned bounds/phase. Uses existing renderer selection and releases pin on all ordinary error paths. Private artifacts only; no default export. Enables comparison of in-process rendering to existing offscreen clipping consumer using identical inputs.

Rebuilt research preview;360refresh reload again96packets/0failures/342renders/1stale suppression. At alpha2/3,3840x2160live final frame and independent offscreen process match exactly0pixels changed. Confirms metadata/phase/order transport and scissor implementation parity for this fixture, not correctness of retained bounds at intermediate pose. No60fps claim.

Next dependency remains sampled visibility/clip recomputation and entrants, with zero-output objects and paced/controller checks outstanding. ROM,saves,fallback,ordinarybridge,timing untouched. Archived live source,CSV,comparison report,VISIBILITY; exported packets/clips/images remain work.

## 2026-09-30 continuation: checked sampled bounds API

Added completed_sampled_bounds accepting coherent sampled pose and exact retained identity. Reconstructs queue/object plans, maps unique source/pass to captured draw ordinals, returns owned4u16bounds per draw, zeros hidden walls and explicitly counts new queued entrants. Ambiguous repeated sources, pass/object mismatch or unsupported multiwall object plans reject atomically. Captured roads retain original bounds. Temporary allocation freed on all paths; no renderer wiring yet.

Research build/850refresh regression passes.17sample outputs exactly match existing diagnostic wall-plan viewports; entrant count matches known candidate admission and wrong-epoch calls preserve bounds/count. Existing206scene publication/material checks pass. This API intentionally cannot solve repeated-source correspondence or insert new geometry, and retained completed history still only2scenes; live resource lifetime extension may be required.

Next dependency: sample-pose/owned-history connection in renderer with explicit handling of entrant count and ambiguous scenes, then general occurrence tracking. ROM,saves,ordinarybridge,fallback,timing unchanged. No playable60claim. Archived bridge/test/report,VISIBILITY.

## 2026-09-30 continuation: renderer/scene lifetime mismatch fixed

Instrumented research render selection for retained pose availability.360refresh reload run exposed34expired scene requests vs309available with prior2scene completed surface history. Extended completed surface audit history to bounded16entries matching snapshot timeline capacity; all related lookup/clear/eviction loops use named capacity. Model-only history remains2unchanged. Extra retained surface snapshots/audits increase memory and are separate from visibility history budget; exact combined footprint not yet measured.

Rebuild and repeat render:343available,0expired,96publications,342renders,0failures,1stale suppression.850refresh provenance regression still passes all206scenes,17samplebounds,eviction/reset and material/order checks. This removes observed lifetime blocker; does not guarantee availability under different publication/failed-allocation patterns or thread concurrency.

Next dependency: sampled-pose bounds in render selection with explicit entrant/ambiguous fallback diagnostics, then candidate integration and paced fullscene verification. ROM,saves,ordinarybridge,fallback,timing untouched; no playable60claim. Archived bridge/live source,CSV,testreport,VISIBILITY.

## 2026-09-30 continuation: sampled bounds in research GPU path

Added optional pair-selection hook to packet preview and --sampled-clips live mode. Retrieves both retained poses, samples shared planar pose at presentation alpha, computes native sampled bounds against older scene, maps ordinal bounds to packet surfaces. Uses a private copied clipping set, never mutates retained metadata. If unavailable/ambiguous or new entrant count nonzero, retains full captured clipping set and counts fallback; does not silently claim entrant support. Export path now recomputes same sampled set when enabled.

Rebuilt diagnostic depth preview and360refresh reload test passes:96packets,342frames,343pose reads available/0expired.337sampled clipping applications,0unavailable,6entrant fallbacks (includes final render in343calls). No publication or lighting failures; reload stale suppression passes. This is unpaced fixture coverage, not fullscene motion correctness; entrants remain missing and captured roads/object eligibility unchanged. Last export-path adjustment is source-only here, pending next rebuild/export parity test.

Next dependency: sampled export parity then candidate geometry/order integration for6entrant fallback frames; broaden repeated sources and zero-output object coverage before paced/controller verification. ROM,saves,ordinarybridge,fallback,timing untouched; no playable60claim. Archived packet/live sources,CSV,VISIBILITY.

## 2026-09-30 continuation: sampled live parity and entrant locations

Rebuilt final export change and added reproducible test_live_sampled_parity.py. Exports exact acquired pair plus sampled bounds, launches separate offscreen sampled consumer, compares full4K image. Added entrant diagnostic lines with epoch/scene pair/alpha/count.

Parity passes0changed pixels at final alpha2/3.96packets,0failures,342renders; export adds one pose/sample call (344pose reads,338sampled applications). Six entrant fallbacks are three distinct phases repeated after reload:27->28 at1/3 and2/3;28->29 at.75, one entrant each. No expired poses/unavailable bounds. This gives concrete earlier-route cases beyond prior140/141candidate fixture. Same-input final parity does not validate missing entrant frames or temporal smoothness.

Next dependency: identify/extract these entrants from older owned scenes and validate per-region insertion, then native candidate packet integration. ROM,saves,ordinarybridge,fallback,timing unchanged; no playable60claim. Archived live source,test/report,CSV,VISIBILITY; private packets/clips/images stay work.

## 2026-09-30 continuation: earlier-route entrant extraction

Sampled preview now audits unmatched queue sources on entrant fallback using older completed snapshot and retained palette bank. All6calls extract owned wall geometry/texture successfully:scene27 source139937788 (two phases),scene28 source139937312 (one phase), repeated after reload. Each is first pass,flags4352,16556byte surface (64x64RGBA plus geometry). Frees extracted surface immediately; no rendering insertion yet and extraction overhead is diagnostic.

Rebuild/live parity test passes:4Kfinal image unchanged,96packets/0failures. Added assertions for6successful exact expected asset records in reproducible test (assertions added after observed passing run). Existing entrant fallback remains explicit. State address chosen from captured walls assumes shared state in this fixture; generic multi-state scene needs stronger association.

Next dependency: validate insertion anchors for both sources and compose candidate geometry/order/lighting/identity sections without borrowing future assets. ROM,saves,ordinarybridge,fallback,timing untouched; no playable60claim. Archived live/test sources,report,VISIBILITY.

## 2026-09-30 continuation: entrant insertion anchor evidence

Added diagnostic anchor recovery from existing first-pass peers in sampled region. Scene27source139937788 anchors before captured command5,descriptor139893648;scene28source139937312 before command11,descriptor139893600. Both anchors are walls, no descriptor ambiguity. Newer captured scene used only as validation reference: candidate immediately precedes corresponding anchor in all6cases. Extraction remains older-owned; future geometry/material never borrowed.

Rebuild/reload/parity test passes0changed final pixels;6extractions and6adjacent-reference matches. Anchor code is diagnostic, not production insertion policy: does not yet reject every nested/deferred/interleaved ambiguity and road-anchor branch untested. Rendering still falls back at these phases.

Next dependency: bounded candidate packet composition and checked native insertion using validated first-pass anchors, then render entrant frames against controls. ROM,saves,ordinarybridge,fallback,timing untouched; no playable60claim. Archived live source/report,VISIBILITY.

## 2026-09-30 continuation: native single-wall packet composer

Added candidate_packet.c optional API inserting one unlit wall into owned NSP1packet before explicit command position. Bounds candidate geometry/texture dimensions,size,count; rejects duplicate full identity; preserves model section,old world records,lighting tables/records and model identity. Adds empty unlit record and candidate identity, adjusts counts, validates complete output through packet builder. All temporaries freed; output arguments unchanged on failure. Caller must prove scene/asset/anchor coherence; no automatic insertion policy yet.

Strict compiler build passes. Native scene140candidate composition test verifies original sections/payload preservation and command insertion before4; truncated surface,invalid anchor and duplicate insertion reject atomically. Uses older-owned candidate fixture. Output remains private work packet; no live preview change this run.

Next dependency: use composer with checked live entrant anchors and sampled clip metadata, validate actual entrant frame images and failure fallback. Lit candidates/multiple entrants and generic repeated regions remain unsupported. ROM,saves,ordinarybridge,fallback,timing untouched; no playable60claim. Archived C/header/test/report,VISIBILITY.

## 2026-09-30 continuation: live entrant packets composed

Optional NF_ENTRANT_EXPORT now composes owned packets inside entrant diagnostic from older scene, extracted candidate, recovered base identity and wall anchor. Only first-pass wall-anchor/no-descriptor-ambiguity branch allowed. Composer linked into separate research preview. All original/candidate/expanded allocations freed; default rendering still fallback, export only on explicit diagnostic environment variable.

Live reload/parity test passes;6packet compositions succeed. Exported27/28packets pass native packet validator, contain correct new surface at commands5/11 with expectedsource identities. Scene28packet1278616bytes. These packets have not been rendered with candidate-specific sampled clips yet. Generic anchor ambiguity and state association limitations remain. Initialized base on failed-read branch after test; no semantic success-path change.

Next dependency: export sampled clip set including candidate and render these exact pairs, then remove entrant fallback only after image/order validation. ROM,saves,ordinarybridge,fallback,timing untouched; no playable60claim. Archived live source,parity/packetreports,VISIBILITY; packets remain private work.

## 2026-09-30 continuation: entrant packets rendered with sampled clipping

Extended optional entrant export with newer pose packet and full sampled clip sidecar, including appended candidate identity/bounds. Rebuilt research preview and reran live reload/parity: six successful compositions, final live/offscreen parity unchanged. Added test_live_entrant_render.py rendering expanded scenes27(alpha2/3) and28(alpha.75) at3840x2160 against identical packets with only candidate clipping hidden. Both pass packet/clip identity validation and strict changed-pixel containment in candidate scissor. Candidate contributes77353pixels (bbox300,681,456,1226) and63382pixels (300,0,352,1234), respectively. Visually inspected both images: textured road/car/walls and entrant at left viewport edge. This does not establish original-game image fidelity, generic insertion order, or temporal correctness.

Exports overwrite earlier phase/epoch for same serial, so scene27alpha1/3 is not covered by this image test. Live preview still retains entrant fallback; exported composed packets are diagnostic only. General nested/deferred anchor ambiguity, state association, lit/multiple candidates, complete object eligibility and paced/controller checks remain. Next dependency: preserve all phase exports and safely bind expanded packet/clips lifetime into opt-in live consumer, with rejection fallback and frame parity tests. ROM,saves,ordinary bridge,stable synchronized fallback and game timing untouched; no playable native60fps claim. Archived source,test/report,parity report and CSV; private packets/images remain work.

## 2026-09-30 continuation: all entrant phases preserved and reload-verified

Changed diagnostic export names to include epoch, scene serial and sampled alpha, avoiding overwrite of scene27alpha1/3. Extended entrant render test to six explicit fixtures (three phases across epochs2/3), twelve4K renders including candidate-hidden controls. All pass identity, positive candidate contribution and exact scissor containment. Newly covered alpha1/3 contributes23691pixels at bbox300,706,353,1224; other phases retain77353/63382pixels. Full RGB image hashes match for each phase across reload. Rebuilt preview and live sampled parity still passes0changedpixels,96publications/0failures,6successful entrant compositions,0expiredposes.

This establishes repeatable diagnostic coverage for all currently observed entrant fallback phases; it does not establish live insertion, generic ordering, original-render fidelity or60fps gameplay. Next dependency remains owned expanded packet/clips lifetime integration into opt-in live consumer with rejection fallback, then direct frame parity. Existing broader anchor/state/lit/multiple candidate limitations remain. ROM,saves,ordinarybridge,stablefallback and timing untouched. Archived updated preview/test,reports,CSV and technical log; private fixtures/images stay work.

## 2026-09-30 continuation: opt-in live entrant ownership and insertion

Added NF_LIVE_ENTRANTS research option. Composes single unlit candidate from older owned scene, computes expanded sampled clips, redirects world/order/lighting for current frame, and retains packet allocation until consumer returns. New optional packet-preview frame-release hook runs after preview memory is cleared and before snapshot release. Candidate audit returns immediately after transfer so expanded count cannot index original identity section. Multi-entrant batches rejected (extra must equal1); existing ambiguity/pass/anchor/extraction checks remain. Optional export no longer required for live insertion; export failures fall back when requested.

Rebuilt and reran360refresh reload with insertion enabled:96packets,342renders,0publication/lighting failures,6applied/6released,0entrantfallback,0expiredposes. Test now asserts applied/released counts and zero fallback when opted in. Final non-entrant image still matches offscreen exactly. This is live consumer integration in an unpaced research preview, not playable native60fps. Direct entrant-frame live/offscreen pixel parity and rejection-injection coverage remain next dependencies. Generic anchor/state association, lit/multiple candidates and full scene/timing/controller verification remain unresolved. Stable fallback,ordinarybridge,ROM,saves and game timing untouched. Archived sources,test/report,CSV and log.

## 2026-09-30 continuation: live entrant frames match replay at4K

Added optional NF_ENTRANT_LIVE_CAPTURE readback at frame release while live framebuffer/context remain valid. Capture filenames include epoch/serial/alpha; allocation freed regardless of file-open success. Added reproducible test_live_entrant_parity.py: runs opt-in live reload/export/capture, regenerates offscreen candidate/control renders, rejects stale outputs by modification time, compares full3840x2160 RGB frames at all six entrant instances.

PASS: scenes27alpha1/3 and2/3,28alpha.75 across epochs2/3 each have0changedpixels between live insertion and exported replay. Underlying tests also pass candidate clipping containment/positive contribution, reload image equality,6applied/6released,0entrantfallback and final-frame parity. Captures add diagnostic readback cost; no performance claims. This verifies selected live geometry/order/clipping agrees with the existing offscreen consumer, not independent original-game fidelity or temporal/gameplay correctness.

Next dependency: inject candidate rejection/failure and verify fallback/ownership, then broaden state/anchor ambiguity and object eligibility before paced fullscene/controller validation. Generic nested/deferred anchors, lit/multiple candidates remain unsupported. ROM,saves,ordinarybridge,stable synchronized fallback and simulation timing untouched. Archived live source,new parity test/report,underlying reports,CSV and technical log; private captures remain work.

## 2026-09-30 continuation: candidate rejection paths exercised

Added research-only NF_ENTRANT_FAULT modes: truncated passes one fewer byte to actual packet composer; after-compose rejects after expanded allocation but before clipping/transfer. Existing unconditional cleanup frees original/expanded/candidate allocations on these paths. Added test_live_entrant_rejection.py with disabled baseline,two injected failures,and enabled run, each360refresh with reload. All4runs complete96publications/342renders without publication failures or expired poses. Each failure rejects6candidates, uses6fallbacks, transfers0frames; after-compose logs positive expanded sizes, truncated logs0. Enabled run applies/releases6. Final non-entrant4K output identical across all4runs.

Limitations: transferred-frame counters are not allocator-level leak detection; cleanup verified by source flow, and fallback entrant-frame pixels not captured by this test. No paced timing or playable claim. Next dependency: tighten candidate state/anchor association beyond current fixture and cover zero-output object invocations; add frame-specific fallback parity if changing failure handling. ROM,saves,ordinarybridge,stablefallback and game timing unchanged. Archived source,rejection test/report and technical log; diagnostic images remain work.

## 2026-09-30 continuation: entrant state bound to retained region peers

Removed last-wall-in-scene state selection. Candidate state now comes from packet identity at each retained peer command occurrence in the sampled region. Checks order index in range,wall kind,source match,nonzero state,and agreement among peers; any inconsistency marks ambiguity and blocks extraction/insertion. Added research state-conflict fault to exercise rejection branch. This narrows association to retained regional peers; it does not resolve all repeated/nested descriptor ambiguities.

Rebuilt preview. Six live entrant4K frames still exactly match exported replays across reload; candidate controls/reload parity pass. Expanded rejection suite now has5runs, including state-conflict:6rejections before packet composition,6fallbacks,0transfers; all runs complete96publications/342renders and final images agree. Fault explicitly forces conflict branch rather than constructing a real mixed-state snapshot; broader multi-state fixture coverage remains required.

Next dependency: validate repeated/nested anchor eligibility and capture zero-output object invocations for complete scene coverage, then paced timing/controller verification. No native playable60fps claim. ROM,saves,ordinarybridge,stablefallback and game timing unchanged. Archived sources/tests/reports/technical log; private render artifacts remain work.

## 2026-09-30 continuation: ambiguous peer occurrences rejected

Tightened entrant anchor recovery: each sampled first-pass peer source must occur once in sampled queue and at most once among all retained wall commands (including object commands); matching object occurrence rejected. Retained peer command positions must increase in sampled order. This prevents arbitrary selection of repeated sources and reversed peer runs before identity/state lookup. Existing descriptor/state checks retained; nested/interleaved region proof is still incomplete, so this remains opt-in research.

Rebuilt and six4K live/replay entrant comparisons remain pixel-exact. Rejection suite expanded to6runs with duplicate-peer count injection: six ambiguous cases reject before composition, fall back, and complete reload run; all other cases pass. Injection exercises multiplicity branch by increasing observed count, not a real repeated-region fixture. Final-frame recovery and transferred-frame release counts remain correct; no allocator instrumentation or paced timing proof.

Next dependency: recover full region occurrence context for nested/interleaved anchors and zero-output object invocations, then broader full-scene/timing/controller tests. ROM,saves,ordinarybridge,stablefallback and game timing unchanged. Archived updated live source,rejection test,reports and log. No playable native60fps claim.

## 2026-09-30 continuation: owned zero-output object invocation capture

Added bounded64-entry per-scene object-region invocation capture at generic region entry from03002364, independently of emitted surfaces. Each448byte record owns object address,state/record addresses,256byte state,164byte object and16byte region record. Completed history copies these records; reset clears pending records. New identity-bound completed_object_invocations API rejects stale identity, insufficient capacity and any capture overflow/read failure without changing outputs. Adds approximately28KiB per completed history entry. Scenes with no captured surfaces still do not create a completed audit entry; this is not universal scene completeness.

Rebuilt research bridge and full206-scene route test passes. Captured194invocations; all194 native region reconstructions exactly match owned record bytes. Five invocation addresses have no emitted object wall in their scene, accounting for194invocations versus189emitted object-wall fixtures. Capacity/wrong-boundary rejection outputs remain unchanged. Existing4234draw/material/order/publication and17sample tests pass. Address-level unmatched count does not disambiguate repeated invocations sharing an address; no sampled eligibility insertion from these new records yet.

Next dependency: evaluate all owned invocations at sampled poses, including five zero-output cases, and bind occurrence context for ordering before live object insertion. Fullscene motion,timing and physical controller checks remain. ROM,saves,ordinarybridge,stablefallback and game timing unchanged. Archived capture header,test/report,technical log. No playable native60fps claim.

## 2026-09-30 continuation: previously invisible object entrants identified

Added completed_object_invocation_plan API indexed by owned invocation rather than emitted draw. Validates epoch/interval/index/capture completeness, uses owned invocation state/object with snapshot planner at requested pose. Route test evaluates194retained invocations and193midpoints between adjacent captured poses; invalid index leaves output unchanged. Retained plans yield5empty cases, matching prior no-emitted-address count. All existing206scene route checks pass.

Concrete new visibility gaps: previously empty invocation0 in scene122 and scene143 each produces1wall at alpha.5 toward next scene. Empty calls in95(index1),96(index0),111(index0) remain empty at midpoint. Overall midpoint empty count4 also includes other visibility changes; do not infer transition count from totals. These two object entrants are not handled by current queue-only live entrant insertion. Test report now records exact transition identities for follow-up.

Next dependency: retain occurrence/order context and extract these two object-wall entrants from older owned snapshots, then test clipped/material-correct insertion before broader paced fullscene/controller checks. Native reconstruction is not independent original-frame correctness proof. ROM,saves,ordinarybridge,stablefallback and timing untouched. Archived header,test/report,technical log. No playable native60fps claim.

## 2026-09-30 continuation: object invocation insertion slots retained

Capture now records emitted-surface count plus already-seen model count at each object-region invocation, independently of whether a wall is emitted. Slots copied with completed ownership; new identity/index-bound slot API rejects invalid requests atomically and requires one captured model. Existing448byte invocation API layout unchanged.

Full206scene route passes. All189emitting object invocations have slots exactly matching their first captured object command;194retained plans/region copies and193midpoint plans remain valid. Empty-to-visible object entrants now have concrete older-scene insertion slots:scene122 invocation0 before command4,scene143 invocation0 before command22. Invalid slot index preserves sentinel. These positions express original invocation order; interaction with additional simultaneous insertions and repeated object addresses still needs explicit handling.

Next dependency: extract material/geometry for these two sampled object walls from owned invocation state and bind to captured slots, then clipped rendering parity. ROM,saves,ordinarybridge,stablefallback and original timing unchanged. Archived header,route test/report and technical log. Fullscene60fps gameplay/controller validation remains outstanding.

## 2026-09-30 continuation: owned object candidate extraction seam

Added identity/index/pose-bound object candidate API. Requires exactly one sampled wall, overlays retained invocation state on older snapshot reads, collects retained draw palettes, then uses existing conservative unlit candidate extractor. Temporary palettes freed; no new rendering or timing path. Route diagnostics now record candidate material plan and extraction result for all five previously empty invocations.

Full206scene route test passes. At midpoint scene122source139970292 extracts16556bytes (64x64RGBA plus geometry), flags8448, deferred pass1. Scene143source139938876 also plans one64x64 wall with flags8448/pass1 but extraction rejects (output remains null/0). Three still-empty invocations reject as expected. Thus existing first-pass queue insertion cannot simply be reused, and scene143 needs rejection-cause investigation (owner/visibility/material/palette stages) before extending support. Extracted scene122surface has not yet been rendered or compared against later captured material; do not treat successful extraction as visual correctness.

Next dependency: identify scene143 extraction rejection and validate resolved material/texture for scene122, then compose with explicit object slots and sampled clips including deferred-pass behavior. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived header,test/report,technical log; extracted private surface remains work. No native playable60fps claim.

## 2026-09-30 continuation: scene143 rejection isolated to palette disagreement

Added optional staged candidate diagnostic API while preserving existing extraction wrapper and atomic surface outputs. Stages distinguish input/owner,visibility,animation,resolved material,dimensions,texture reads,palette agreement and final surface extraction. Research object candidate exposes latest synchronous stage (9 for unavailable/no-single-wall before extraction); not a thread-safe per-request diagnostic channel.

Rebuilt bridge/full206scene route tests pass. Scene122 extracts atstage0;scene143 rejects atstage7: texture reads and material lookup succeed, but retained draw palettes disagree on at least one used texture index. Three empty object plans reportstage9. Conservative rejection remains intact; selecting arbitrary first palette would risk wrong colors. No rendering changes this run.

Next dependency: capture/select palette at object invocation's actual draw-order position, including zero-output calls, then validate scene143 color extraction and scene122material fidelity before object packet insertion. Existing global palette agreement is intentionally insufficient for this case. ROM,saves,ordinarybridge,stablefallback and original timing unchanged. Archived native source/header,capture header,test/report and log. No playable native60fps claim.

## 2026-09-30 continuation: invocation palette is not always draw palette

Added owned512byte palette capture per object invocation, copied into completed history with identity/index-bound read API and atomic invalid-index rejection. Existing448byte invocation record layout remains unchanged; extra storage32KiB per completed entry. Capture failure/overflow still rejects whole invocation set. No change to candidate palette selection.

Attempted equality check against emitted object draw palettes failed. Converted it to explicit diagnostic counts (not a passed equivalence claim): full206scene route completes with123exact palette matches and66differences among189emitting invocations. All194invocations captured; existing material/order/visibility checks pass. Thus generic-region entry palette cannot be assumed to be the palette at wall draw, and switching scene143 extraction to that palette would be unjustified. Difference counts include all512bytes; whether differences touch each texture's used indices remains unmeasured.

Next dependency: compare used texture indices and trace palette changes between invocation and wall draw; reconstruct appropriate per-object/material palette before relaxing conservative extraction. Scene143 remains rejected. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived capture header,test/report and log. No native playable60fps claim.

## 2026-09-30 continuation: object palette differences are transparent-index only

Extended route audit to read each emitted object's actual indexed texture, verify its hash against retained draw provenance, and compare only used palette entries. Records exact changed indices per invocation. Full206scene test passes:66used-palette differences, all exclusively index0; all189object draws have identical colors at used nonzero indices. native_surface.c wall RGBA assigns alpha0 to texture index0, so these observed differences do not affect visible unlit wall texels. Prior concern about visible color mismatch from invocation palettes is narrowed by this evidence, not by assuming palette equality.

Candidate palette helper still includes index0 in global agreement, and scene143 remains rejected. This run does not establish that scene143's all-draw-bank disagreements are also exclusively transparent or that lit lookup tables are interchangeable. Next dependency: evaluate candidate-specific nonzero-index agreement and introduce a wall-specific transparent palette policy only with tests preserving generic palette semantics, then extract/render scene143. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived updated route test/report/log. No native playable60fps claim.

## 2026-09-30 continuation: transparent wall palette policy resolves object extraction

Added separate nf_wall_candidate_palette policy: ignores transparent index0 but still requires agreement for every used nonzero index. Generic nf_candidate_palette retains its stricter index0 semantics. Unlit candidate extraction now uses wall policy; lit/extended-UV restrictions unchanged. Component tests pass generic-zero rejection,wall-zero acceptance,visible mismatch atomic rejection,unused mismatch acceptance and empty-input rejection.

Research bridge rebuild/full206scene route pass. Both object entrants (122source139970292 and143source139938876) now extract16556bytes atstage0 from older owned data. Scene143's prior rejection was therefore transparent-index disagreement in retained palette bank. Three zero-draw invocations still reject. Six existing live queue-entrant4K comparisons remain pixel-exact across reload. Object surfaces themselves still need packet/clipping/render validation; no claim of completed object insertion or original-frame fidelity.

Next dependency: compose both object surfaces at captured slots4/22 with matching midpoint clip metadata and render against controls, then integrate into live visibility accounting. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived native source/header,policy test/report,route/live reports and technical log. No playable native60fps claim.

## 2026-09-30 continuation: object entrant packets rendered

Route exporter now preserves older/newer packets,owned candidate identity,original invocation slot and sampled ordinal/candidate bounds for122/143. New test_object_candidate_render.py composes candidates via native packet API, maps original ordinal bounds to packet indices, renders4Kshown/hidden controls atalpha.5.

Both consumers accept packets/clips. Scene122candidate changes27745pixels atbbox300,0,318,1542; sampled queue has0additional entrants. Scene143candidate changes0pixels in this composed scene, and sampled queue reports4additional entrants not included in this single-object diagnostic. Do not treat zero difference as verified visibility/fidelity: candidate bounds are narrow[2,4,0,158], and clipping/occlusion/geometry require investigation with the complete sampled scene. Route regression passes. No live object integration yet.

Next dependency: investigate scene143zero contribution with its4queue entrants and verify scene122clipping/control containment before live insertion. ROM,saves,ordinarybridge,stablefallback and timing untouched. Archived route exporter,new render test/reports and log; private packets/images remain work. No playable native60fps claim.

## 2026-09-30 continuation: object clipping controls narrowed zero-pixel case

Extended object render test with candidate-only full-viewport clipping control and strict changed-pixel containment in sampled scissor. Six4Krenders pass. Scene122contributes27745pixels both with sampled bounds and full viewport; all changes lie within sampled scissor. Scene143remains0changedpixels even with candidate scissor expanded to full viewport. Thus narrow sampled scissor alone does not explain this diagnostic's zero contribution; depth occlusion,projection/geometry or transparent texture coverage remain candidates. Its4missing queue entrants still prevent complete-scene fidelity conclusions.

Next dependency: inspect scene143camera-space candidate geometry,coverage and depth against retained scene before live object integration. Rendering clipping has not been relaxed in the live path. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived updated control test/report and technical log. No native playable60fps claim.

## 2026-09-30 continuation: object entrant projection diagnostics

Added test_object_projection.py using native shared rigid scene transform,actual packet camera poses and projection,near-plane64 clipping,and candidate RGBA alpha coverage. Corrected initial diagnostic vertex parsing to match planar xyz array followed by UV array (24byte vertex stride); no renderer/source geometry changed.

Scene122crosses near plane and projects only about1.35GBApixels into left viewport, consistent with narrow visible rendered strip. Scene143is fully in front (depth8114..9353),projects x[-34.12,3.36],y[72.00,88.56]; only a small left-edge sliver enters viewport. Its texture has1310opaque of4096texels (122has1304),so not globally transparent. This rules out fully-behind-camera or wholly-transparent-texture explanations, but does not distinguish local transparent coverage from depth occlusion. Sampled143scissor begins atx2,leaving approximately1.36GBApixels of geometric overlap.

Next dependency: isolate candidate-only rendered coverage/local UVs and depth occluder in143 before composing its4queue entrants and live object insertion. Existing4Kcontrol findings unchanged. ROM,saves,ordinarybridge,stablefallback and timing untouched. Archived projection diagnostic/report/log. No native playable60fps claim.

## 2026-09-30 continuation: scene143candidate has isolated visible coverage

Added compile-time diagnostic command filter and separate isolated-clip-preview.exe selecting one packet surface; normal consumers compile without filter. Extended object test to shown,hidden,full-viewport,and isolated shown/hidden pairs. Ten4Krenders pass. Scene122isolated contribution remains27745pixels,identical bbox to full scene. Scene143isolated full-viewport candidate contributes2119pixels atbbox300,1009,345,1190 while full-scene contribution remains0 even with widened clipping.

This establishes visible textured candidate coverage and strongly indicates coverage by existing scene geometry rather than globally transparent/offscreen candidate. Exact occluder/depth relation remains unmeasured; do not infer full-scene correctness from zero contribution, especially with4missing queue entrants. Captured invocation insertion slot remains22. Next dependency: enumerate/compose all sampled entrants for143 and validate ordering/occlusion, then live object integration. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived diagnostic hook sources,test/report/log. No native playable60fps claim.

## 2026-09-30 continuation: scene143queue entrants enumerated and extracted

Extended route exporter to enumerate sampled queue source/pass pairs absent from older retained non-object commands, verify count against native sampled-bounds entrant count, and extract each candidate from older scene. Scene143has4first-pass/unlit flags4352entrants:139910928(queue6,region17,128x64,32940bytes),139911132/139911200(queue9,region18,64x64,16556bytes each),139910724(queue11,region16,64x64,16556bytes). All4extract successfully using retained palette policy. Full206scene route suite passes; scene122queue candidate list empty as expected.

Exported per-candidate region records,material/texture plan and success sizes for reproducible composition. Current missing-key comparison is source/pass based; repeated identical source/pass in different region occurrences still requires stronger association. These4queue surfaces are not yet inserted or rendered together; only original single-object diagnostic exists. Next dependency: derive occurrence-aware original-command insertion anchors and compose4queue+1object candidates while preserving their order, then inspect scene143occlusion. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived exporter,route report,queue metadata and log; private surfaces remain work. No native playable60fps claim.

## 2026-09-30 continuation: scene143requires new-region handling

Exported captured and sampled full queue plans for object replay fixtures; added topology audit. Scene143queue grows10->12records at midpoint. New regions18(sampled index9,depth4,2walls) and16(index11,depth5,1wall) account for3of4queue entrants. Region17already exists and gains139910928 before retained139910996 at original command3. Regions18/16have no retained region commands, so peer-based anchor recovery cannot place them safely. Region89also appears twice with differingflags/records, reinforcing need for occurrence-aware traversal.

Full206scene route test and topology assertions pass. Crucially, four missing wall surfaces are not necessarily the whole scene delta: newly visible regions may also require road/object emission. Do not call wall-only composition complete. Next dependency: reconstruct original region traversal/emission (including empty/new regions and roads), or capture region invocation order before assigning anchors for18/16. Candidate-only object rendering evidence unchanged. ROM,saves,ordinarybridge,stablefallback and timing untouched. Archived exporter,topology test/report,route report/log; queue binary fixtures remain private work. No playable native60fps claim.

## 2026-09-30 continuation: complete bounded region invocation trace

Added per-scene generic-region entry/return trace independent of emitted walls/roads. Each9word record owns region16bytes,callerLR,pass,start/end command slots and nesting depth. Bounded256records/64stack; overflow,read failure,unbalanced return or unfinished stack marks trace invalid. Completed history owns copies; new identity/capacity-bound API exposes records. Pending reset clears trace. Additional9KiB per completed entry. Trace only covers stage3 audited scenes retained with surfaces, not every game mode.

Research bridge rebuild/full206scene route passes:3509region invocations,1481with empty command ranges. Every range is ordered and inside completed command count; traces all close cleanly. Existing object/material/order/publication tests pass. Saved143/144invocation sequences in report for traversal reconstruction, including previously invisible calls. This is captured occurrence context, not a sampled native traversal implementation.

Next dependency: compare captured generic invocation order against queue/dependency reconstruction and use it to specify sampled emission for new18/16regions (including roads/objects), then render combined143scene. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived capture header,test/report/log. No playable native60fps claim.

## 2026-09-30 continuation: root traversal recovered across route

Added independent root invocation reconstruction to route test: iterate queue records in reverse order excluding flags&8, first pass0/caller03004da4,then pass1/caller03004de8. Exact full16byte records,pass and caller sequence match captured depth0trace in all206scenes,including repeated region records. Nested invocations remain outside this rule and retain separate captured context.

Applied rule to143midpoint: root region order becomes16,21,18,237,17,238,89,22,289,87,88 in each pass. Subsequent scene144captured commands confirm regions16/18each emit a road as well as their1/2walls (descriptors139890192/139890288). This supports need for road entrants but does not prove midpoint road eligibility without sampled reconstruction. New-region insertion requires these region blocks before older root blocks21/237,not arbitrary nearest wall matching.

Next dependency: implement native root schedule and sampled road emission/material extraction for16/18, preserving nested/object calls,then compose midpoint scene. Full206route checks pass. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived updated route test/report/log. No native playable60fps claim.

## 2026-09-30 continuation: native root region scheduler implemented

Added nf_root_region_schedule in ordered_dispatch module. Copies bounded20record queue into owned max40call schedule,reverse order for each pass,skips flags&8,retains queue occurrence index and full record so duplicate regions remain distinct. Invalid count/null input rejects atomically; zero count supported. Explicitly does not infer nested calls,road/object eligibility or surface order within region.

Research bridge rebuilt/full206scene route passes. Native output matches every captured depth0record/pass sequence and original queue occurrence (206exact schedules);412invalid-input checks preserve output. Existing3509invocation/material/order/publication checks pass. This replaces test-only root rule with callable native component; live renderer still uses existing publication path.

Next dependency: sampled road emission/extraction for newly visible16/18regions and nested/object scheduling before combined143render/live integration. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived C/header,test/report/log. No native playable60fps claim.

## 2026-09-30 continuation: native road material selection recovered

Inspected original ARM road branch03002998..03002a0c. Implemented descriptor+8 material/animation selection in nf_road_material_plan with bounded reads/address arithmetic and atomic5word output (resolved descriptor,animation pointer,texture,shift,stored height). Added identity-bound completed-scene wrapper using owned snapshot. This selects material only, not road geometry eligibility; descriptor+4 alternate branch remains unsupported by extractor.

Research rebuild/full206scene route passes. All1058captured road draws match native animation pointer and texture dimensions/address against retained draw arguments/provenance. Existing scene/order/object tests pass. This establishes material inputs needed for road candidates without borrowing later scene assets. Visibility depends on earlier geometry result/branch and still needs sampled evaluation.

Next dependency: reconstruct road eligibility from sampled region geometry and extract16/18road candidates using verified material plan plus coherent palette,then full scene composition. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived native source/header,capture wrapper,test/report/log. No playable native60fps claim.

## 2026-09-30 continuation: sampled new-region road geometry/material inputs

Traced original generic branch: road preparation gated by descriptor+8/+4 material presence after region transform; wall dispatch result replaces deferred mask but cmp uses preexisting material-presence flag. Added route fixture export querying full sampled region reconstruction and native material plan for each queue candidate region.

Full206scene route passes. At143midpoint newregion18produces5stream vertices,primarymaterial115,alternate0,texture138010076,width256,storedheight128;newregion16produces6vertices,material116,alternate0,texture138042844,width256,storedheight512. Existingregion17produces4vertices,material117. This establishes usable sampled geometry/material inputs,not exact raster dispatch eligibility inside030032f0. Road extractor halves stored height as existing packed-road convention.

Next dependency: construct synthetic road material context from these plans,resolve opaque road palette coherently (index0must not be ignored),extract/render candidates,then prove dispatch/ordering. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived route test/report,road metadata/log. No native playable60fps claim.

## 2026-09-30 continuation: new-region road surfaces extracted

Implemented conservative primary-road candidate extractor using verified material plan and synthetic material context. Reads packed road texture,compares palettes on actually sampled first-half scanline indices (including opaque index0),then invokes existing road geometry/UV extractor. Owned-scene wrapper gathers retained palettes; all temporary texture/palette buffers freed. Does not decide visibility or support alternate descriptor+4 branch.

Research rebuild/full206scene route passes. Scene143road candidates extract forregion18(65748bytes,256x64),region16(262396bytes,256x256),and controlregion17(262316bytes). Control17matches captured old packet surface byte-for-byte including geometry,UV andRGBA. New16/18roads are not yet independently image-validated. Palette agreement succeeds without ignoring opaque index0.

Next dependency: extend packet composition for road kind with correct identity/lighting handling,insert new region blocks in native root order,then combined1434Kcontrols and sampled eligibility validation. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived native source/header,wrapper,test/reports,road metadata/log; private assets remain work. No playable native60fps claim.

## 2026-09-30 continuation: native road packet composition

Refactored candidate packet composer through shared internal unlit-surface insertion; existing wall API still requireskind2,new road API requireskind1. Both preserve model,existing surfaces/identities/order,lighting records and reciprocal table; append empty lighting record for new surface and keep atomic failure/free contract. No live consumer changes.

Strict compiler build passes. Existing wall composer regression passes. New road test inserts16/18surfaces and checks geometry/UV/RGBA section preservation,order permutation,newidentity/model identity and lighting/table preservation. Six malformed/truncated,duplicate,andwrongkind cases reject atomically. Test uses command0 solely to validate structure,not real region placement. Newly inserted roads not rendered this run.

Next dependency: compose143newregion blocks in verified root order (16wall+road before21;18walls+road before237),adjust remaining wall/object slots coherently,then4Kcontrols. Road eligibility/nested emission coverage still needs validation. ROM,saves,ordinarybridge,stablefallback and timing unchanged. Archived composer/header,test/reports/log. No playable native60fps claim.
