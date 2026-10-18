#ifndef NF_NATIVE_VISIBILITY_H
#define NF_NATIVE_VISIBILITY_H
#include <stdint.h>
#include "visibility_capacity.h"
#include <stddef.h>
/* Reader must serve one immutable snapshot and return nonzero only when the
   full requested range was copied. It must not reenter a running emulator. */
typedef int (*NFVisibilityRead)(void*,uint32_t,void*,size_t);
/* Source-list cursor, separate from global visit bitmap and sorted links.
   Advance consumes CURRENT object's post-callback bytes; never caches +02.
   1 current object, 0 FFFF end, -1 invalid/cycle. Failure preserves cursor. */
typedef struct {uint32_t current,count;uint8_t seen[512];} NFVisibilityObjectCursor;
int nfs_visibility_object_cursor_begin(NFVisibilityObjectCursor*cursor,unsigned head,unsigned count);
int nfs_visibility_object_cursor_advance(NFVisibilityObjectCursor*cursor,const uint8_t object[164]);
/* Zero-initialize collector, then initialize cursor. step returns2 to request
   callback selector for cursor.current. Caller applies callback effects to
   supplied buffers/matrix, then calls step again to resume. 1 processed,0 end,
   -1 invalid. Failure is terminal; earlier visitation/callback changes remain.
   No simulation callback is invoked by this API. */
typedef struct {NFVisibilityObjectCursor cursor;unsigned awaiting_callback;} NFVisibilityObjectCollector;
int nfs_visibility_object_collect_step(NFVisibilityObjectCollector*collector,uint8_t*objects,uint8_t*visited,size_t visited_bytes,const uint32_t matrix[12],uint32_t*head,uint32_t*maximum,uint32_t*callback);
typedef struct {uint32_t offset,before,after;} NFVisibilityObjectDelta;
/* Apply only callback-changed bitmap/matrix/list globals. All changed values
   must match before; failure preserves every output. Object deltas separate. */
int nfs_visibility_callback_state(uint8_t bits[32],uint32_t matrix[12],uint32_t globals[2],const uint8_t before_bits[32],const uint8_t after_bits[32],const uint32_t before_matrix[12],const uint32_t after_matrix[12],const uint32_t before_globals[2],const uint32_t after_globals[2]);
/* Object-buffer callback deltas only. Caller verifies scene identity separately.
   Requires pending matching object/selector and expected old bytes; rejects
   duplicate offsets. Up to256 changes, atomic failure; does not resume step. */
int nfs_visibility_object_callback_apply(const NFVisibilityObjectCollector*collector,uint8_t*objects,unsigned index,unsigned selector,const NFVisibilityObjectDelta*deltas,unsigned count);
/* Object visit gate2000..2090. Marks first visit even for inactive object.
   Returns1 active first visit,0 skip,-1 invalid. callback=selector orFFFF.
   Caller must execute authorized callback before rereading flags for sorting. */
int nfs_visibility_object_visit(uint8_t*visited,size_t visited_bytes,unsigned index,const uint8_t object[164],uint32_t*callback);
/* Object flag10 selects region at object+36, inheriting state E2..E8 bounds.
   Original2320..2360; flags/depth zero,parent FFFF. 1 emitted,0 other path,
   -1 invalid. Does not implement object list traversal or projection. */
int nfs_visibility_object_region(const uint8_t state[256],const uint8_t object[164],uint8_t record[16]);
/* Object planar camera position and wrapped squared distance (20A0..20F0).
   out=X,Z,distance; object positions are fixed8. No object mutation. */
int nfs_visibility_object_distance(const uint32_t matrix[12],const uint8_t object[164],uint32_t out[3]);
/* Draw setup2284..2320: planar camera XYZ and horizontal region bounds.
   Vertical bounds remain inherited. No projection/material/draw callbacks. */
int nfs_visibility_object_draw_setup(uint8_t state[256],const uint8_t record[16],const uint8_t object[164],const uint32_t matrix[12],uint32_t xyz[3]);
/* Non-region object gate2368..23B8. Parameters Y,Z,scale,centerY,top,bottom;
   top/bottom are zero-extended state halfwords. 1 visible,0 culled,-1 invalid. */
int nfs_visibility_object_visible(const uint32_t params[6],const uint32_t reciprocal[8192]);
/* Material selection23B8..2410. Marks object flag4, combines material/animation
   indices and distance detail choice. out=material address,effective depth.
   Address arithmetic wraps like ARM; caller validates before dereferencing. */
int nfs_visibility_object_material(uint8_t object[164],uint32_t base,uint32_t depth,uint32_t out[2]);
/* 2410..2460/2588: texture pointer and branch(1=2460,0=2588).
   previous is material-32; only required for flag8 with signed depth>1024.
   Addresses wrap; caller validates mapped assets. Failure preserves out. */
int nfs_visibility_object_texture(const uint8_t object[164],const uint8_t material[32],const uint8_t previous[32],uint32_t texture_base,uint32_t depth,uint32_t out[2]);
/* Nonregion2368..245C composition from owned state/object/XYZ. out=material
   address,effective depth,texture,billboard branch.1 ready,0 culled,-1 invalid
   or unavailable. Object flag update and output publish only when ready. */
__declspec(dllexport) int nfs_visibility_object_material_plan(const uint8_t state[256],uint8_t object[164],const uint32_t xyz[3],NFVisibilityRead,void*,const uint32_t reciprocal[8192],uint32_t out[4]);
/* Alternate path2460..24D8 rectangle. params=X,Y,Z,scale,centerX,centerY;
   out=left,right,top,bottom. Original wrapped fixed-point projection.
   Invalid depth preserves output. No clipping/texture coordinates/drawing. */
int nfs_visibility_object_rect(const uint8_t object[164],const uint8_t material[32],const uint32_t params[6],const uint32_t reciprocal[8192],uint32_t out[4]);
/* Model branch2588..2628 context[68], preserving untouched bytes.
   params=effective depth,projection context,texture,scale. 1 ready,0 slotFF
   hidden,-1 read/invalid failure. Context publication is atomic. */
int nfs_visibility_object_model_context(const uint8_t state[256],const uint8_t object[164],const uint8_t material[32],const uint32_t params[4],NFVisibilityRead read,void*user,uint8_t context[68]);
/* Model context from native material-plan[4], resolving owned material and
   projection scale through reader.1 ready,0 hidden,-1 invalid/unavailable.
   Preserves unused seed bytes and publishes only ready context. */
__declspec(dllexport) int nfs_visibility_object_model_plan(const uint8_t state[256],const uint8_t object[164],const uint32_t plan[4],NFVisibilityRead,void*,uint8_t context[68]);
/* Insert candidate in original descending-distance list (20F8..21F8).
   Objects are count*164 bytes, candidate distance already at+28, identity
   halfword+0 equals index. head FFFF denotes empty. Atomic invalid failure. */
int nfs_visibility_object_insert(uint8_t*objects,unsigned count,unsigned candidate,uint32_t*head,uint32_t*maximum);
/* Post-callback 2090..21F8: reread flags, compute/store distance even behind
   camera, insert only positive depth. 1 inserted,0 skipped,-1 invalid atomic.
   Input objects/matrix must reflect completed callback effects. */
int nfs_visibility_object_sort(uint8_t*objects,unsigned count,unsigned candidate,const uint32_t matrix[12],uint32_t*head,uint32_t*maximum);
/* Sorted +04 draw links from one owned completed collection snapshot.
   Preserves duplicate source occurrences across separate plans; rejects cycles,
   out-of-range links and insufficient capacity atomically. No draw execution. */
__declspec(dllexport) int nfs_visibility_object_sorted_plan(const uint8_t*objects,unsigned count,unsigned head,uint32_t*out,unsigned capacity,unsigned*out_count);
/* Pass-zero recursive links: flag8 replaces own draw with +24 sibling chain;
   otherwise +6 is one post-surface child. Caller handles hidden/transform
   gates and recursion. Reject cycles/out-of-range; atomic outputs. */
int nfs_visibility_region_links(const uint8_t state[256],const uint8_t descriptor[48],NFVisibilityRead read,void*context,uint32_t*out,unsigned capacity,unsigned*out_count,unsigned*replaces_self);
typedef struct {uint32_t edge,resolved_material,texture,shift,height,flags;} NFVisibilityWallDraw;
/* Original264C leaf dispatch, without rasterization. second_pass is the first
   pass deferred mask (not a boolean). Atomic command/count/mask publication. */
int nfs_visibility_wall_draw_plan(const uint8_t state[256],const uint8_t*vertices,unsigned count,const uint8_t*scratch,uint32_t second_pass,NFVisibilityRead read,void*context,NFVisibilityWallDraw*out,unsigned capacity,unsigned*out_count,uint32_t*deferred);
/* Wall UV scratch setup 03001A7C..03001B0C. Inputs are a 68-byte source,
   32-byte resolved material, explicit U base/V offset and U extent. Preserves
   all scratch fields except flags and six UV words. Does not clip/project. */
int nfs_visibility_wall_uv(const uint8_t source[68],const uint8_t material[32],uint32_t u_base,uint32_t v_offset,uint32_t u_extent,uint8_t scratch[52]);
/* Resolve wall material/animation and endpoint height offsets (1958..1B0C).
   bases: top,bottom; heights: current top,bottom,next top,bottom. Publishes
   heights and UV scratch together. No projection or near-plane clipping. */
int nfs_visibility_wall_prepare(const uint8_t state[256],const uint8_t source[68],const uint8_t next[68],const uint32_t bases[2],NFVisibilityRead read,void*context,uint32_t heights[4],uint8_t scratch[52]);
/* Near clipping 1B0C..1CA0, including helper1638. attributes: current A/B,
   next A/B (source+20/+24); heights use wall_prepare order. Returns 1 visible,
   0 both behind, -1 invalid. Both-behind/invalid preserve buffers. */
int nfs_visibility_wall_clip(uint8_t scratch[52],uint32_t heights[4],uint32_t attributes[4],int near_depth,unsigned source_flags,unsigned region_flags,const uint32_t reciprocal[32768]);
/* Project already near-clipped wall scratch; params=scale,centerX,centerY,
   viewportLeft,viewportRight. Original1CB4..1FA8 excluding surface vertex
   emission1D34..1EC8. Returns1 published,0 invalid (unchanged). Rejection is
   scratch flag4, not a failure return. Depths must be positive signed halves. */
int nfs_visibility_wall_project(uint8_t scratch[52],const uint32_t params[5],const uint32_t reciprocal[32768]);
/* Surface stream1D34..1EC8 from near-clipped, not yet projected scratch.
   params=scale,centerX,centerY,Ushift,Vmultiplier,affine. Emits clipped start
   when flag8, then end (24 bytes each). Affine retains existing reciprocal
   field. Capacity is bytes; all outputs unchanged on failure. */
int nfs_visibility_surface_vertices(const uint8_t scratch[52],const uint32_t heights[4],const uint32_t attributes[4],const uint32_t params[6],const uint32_t reciprocal[32768],uint8_t*out,size_t capacity,unsigned*out_count);
/* Complete03001800 scratch plus surface stream/count from transformed ring.
   State F2, scratch and stream publish together; buffers must not overlap. */
int nfs_visibility_region_geometry(uint8_t state[256],const uint8_t descriptor[48],const uint8_t*vertices,unsigned count,unsigned queue_flags,NFVisibilityRead read,void*context,const uint32_t reciprocal[32768],uint8_t*scratch,size_t scratch_bytes,uint8_t*surface,size_t surface_bytes);
/* Single nonrecursive region: setup, native transform and complete geometry.
   Returns1 published,0 hidden/far rejected,-1 invalid/read/capacity failure.
   All non-success paths preserve all caller outputs. No object/draw dispatch. */
int nfs_visibility_region_reconstruct(uint8_t state[256],const uint8_t record[16],NFVisibilityRead read,void*context,const uint32_t reciprocal[32768],uint8_t*scratch,size_t scratch_bytes,uint8_t*surface,size_t surface_bytes);
/* Compose wall scratch preparation over a transformed ring. Does not emit
   the accompanying surface vertex stream or modify state+F2. Atomic failure. */
int nfs_visibility_region_walls(const uint8_t state[256],const uint8_t descriptor[48],const uint8_t*vertices,unsigned count,NFVisibilityRead read,void*context,const uint32_t reciprocal[32768],uint8_t*scratch,size_t scratch_bytes);
/* Original 03004D5C queue dispatch order, excluding global draw-scratch clear
   and leaf drawing. out pairs are (queue index, pass), up to 40 calls. capacity
   counts pairs. Invalid/capacity failure preserves out and out_count. */
int nfs_visibility_draw_plan(const uint8_t queue[NF_VISIBILITY_QUEUE_BYTES],unsigned count,uint32_t*out,unsigned capacity,unsigned*out_count);
/* Region setup 030027F0..030028C8. Returns 1 prepared, 0 material-hidden,
   -1 unavailable/invalid. State[256], viewport[16], descriptor[48], and geometry
   (vertex address,count) publish only on 1. No leaf drawing or recursion. */
int nfs_visibility_region_setup(uint8_t*state,const uint8_t record[16],NFVisibilityRead read,void*context,uint8_t viewport[16],uint8_t descriptor[48],uint32_t geometry[2]);
/* Original 03000D48 ring transform. scratch is count*52 bytes, initialized by
   caller; untouched fields remain intact. 1 completes cyclic endpoint links,
   0 reproduces far-depth stop with partial scratch writes, -1 invalid/read
   failure preserves all scratch. vertices contains count*68 bytes, count<=32. */
int nfs_visibility_region_transform(const uint8_t*state,const uint8_t*vertices,size_t vertex_bytes,unsigned count,NFVisibilityRead read,void*context,uint8_t*scratch,size_t scratch_bytes);
/* Original visibility seed (8,0,80) transformed by 12-word fixed14 affine
   matrix. Output is integer XYZ; multiply/add operations wrap at 32 bits. */
int nfs_visibility_offset(const uint32_t matrix[12],uint32_t out[3]);
/* Original fixed14 yaw matrix plus negative integer camera position. angle
   wraps to 14 bits; half-sine table contains 8192 signed 16-bit samples. */
int nfs_visibility_view_matrix(uint32_t angle,const uint32_t position[3],const int16_t table[8192],uint32_t out[12]);
/* Original local region selector. Reads current region at state+EA and world
   point at +C0/+C8. Success writes region or FFFF, failure preserves output.
   Does not implement the enclosing Thumb fallback or change state. */
int nfs_visibility_select(const uint8_t*state,NFVisibilityRead read,void*context,uint32_t*out);
/* Ordered two-hop fallback, same read/output contract as local selection. */
int nfs_visibility_fallback(const uint8_t*state,NFVisibilityRead read,void*context,uint32_t*out);
/* Thumb 08002D06..08002D92: point[4]=base X/Z (fixed8), offset X/Z
   (integer). out[2]=positive-side region, opposite-side local result.
   Positive side tries local, two-hop, then selected. Opposite may be FFFF.
   Success publishes state[256] and out together; failures change neither. */
int nfs_visibility_pair(uint8_t*state,unsigned selected,const uint32_t point[4],NFVisibilityRead read,void*context,uint32_t out[2]);
/* 08002CB4..08002D92 composition. selected is retained unless base local
   lookup misses, when recovery replaces it. base[2] is fixed8 X/Z.
   Publishes state, selected and pair together. Recovery source is external. */
int nfs_visibility_query(uint8_t*state,uint32_t*selected,unsigned recovery,const uint32_t base[2],const uint32_t matrix[12],NFVisibilityRead read,void*context,uint32_t out[2]);
/* Oriented boundary test, not complete spatial selection. Up to 32 records of
   68 bytes. Success writes descriptor or FFFF; invalid input preserves out.
   Empty rings reproduce original vacuous acceptance without reading vertices. */
int nfs_visibility_contains(const uint8_t*vertices,size_t bytes,unsigned count,uint32_t x,uint32_t z,unsigned descriptor,uint32_t*out);
/* Reconstruct root[16] from selected descriptor, optional redirect and retained
   viewport bounds. This does not perform spatial descriptor selection. */
int nfs_visibility_root(const uint8_t*state,unsigned selected,NFVisibilityRead read,void*context,uint8_t*out);
/* Choose from pair (first unless FFFF, then opposite) and apply descriptor+22
   redirect to an already initialized root[16]. Preserve remaining root bytes.
   selected stores the unredirected region. Failure changes neither output. */
int nfs_visibility_choose_root(const uint8_t*state,const uint32_t pair[2],NFVisibilityRead read,void*context,uint32_t*selected,uint8_t root[16]);
/* Mutable, nonoverlapping buffers: state[256], queue[NF_VISIBILITY_QUEUE_BYTES], groups[4096].
   queue[0..15] must contain the original initialized root record. Reciprocal
   table has 32768 uint32 entries. Returns 0 without modifying any output on
   invalid/unrepresentable geometry or failed reads; 1 publishes all outputs.
   Implements queue builder only, not object rendering or root selection. */
int nfs_visibility_build(uint8_t*state,uint8_t*queue,uint8_t*groups,NFVisibilityRead read,void*context,const uint32_t*reciprocal);
/* Initialize root from retained viewport and selected pair, then build queue.
   Publish state[256], queue[NF_VISIBILITY_QUEUE_BYTES], groups[4096], selected together. Reader must
   serve immutable descriptor/geometry/view inputs. Pair calculation is external. */
int nfs_visibility_build_pair(uint8_t*state,uint8_t*queue,uint8_t*groups,const uint32_t pair[2],uint32_t*selected,NFVisibilityRead read,void*context,const uint32_t*reciprocal);
/* One immutable snapshot, two explicit matrix versions. State must already
   contain intended projection/viewport setup. Query uses original reader;
   builder overlays view_matrix at state+54's address without modifying RAM.
   All four mutable outputs publish together; camera-input policy is external. */
int nfs_visibility_evaluate(uint8_t*state,uint8_t*queue,uint8_t*groups,uint32_t*selected,unsigned recovery,const uint32_t base[2],const uint32_t query_matrix[12],const uint32_t view_matrix[12],NFVisibilityRead read,void*context,const uint32_t*reciprocal);

/* params: signed depth, original sb branch flag, texture base, current texture.
   out: UV width/height, texture, stride, material height, material byte offset. */
int nfs_visibility_object_billboard_material(const uint8_t material[32],const uint8_t next[32],const uint32_t params[4],uint32_t out[6]);

/* rect L,R,T,B; uv U,V,width,height; bounds L,R,T,B.
 out x,y,pixel-pairs,rows,U16,V16,dU-pair,dV-row. -2 unsupported dimensions. */
int nfs_visibility_billboard_clip(const uint32_t rect[4],const uint32_t uv[4],const uint16_t bounds[4],const uint32_t reciprocal[32768],uint32_t out[8]);

/* params: X,Y,Z,scale,centerX,centerY,sb flag,texture base,current texture.
 out: rect[4], material[6], clip[8]; only published on success. */
int nfs_visibility_object_billboard_prepare(const uint8_t object[164],const uint8_t material[32],const uint8_t next[32],const uint32_t params[9],const uint16_t bounds[4],const uint32_t reciprocal[32768],uint32_t out[18]);
/* Billboard rectangle/material/clip from owned native material-plan[4] and
   XYZ. Resolves projection/current/optional next material via reader. Uses
   existing prepare return codes; -2 wrong branch/unavailable input. Atomic out. */
__declspec(dllexport) int nfs_visibility_object_billboard_plan(const uint8_t state[256],const uint8_t object[164],const uint32_t xyz[3],const uint32_t plan[4],NFVisibilityRead,void*,const uint32_t reciprocal[32768],uint32_t out[18]);
/* Diagnostic original-resolution byte-lane raster; validates all accesses before writing. */
int nfs_visibility_billboard_raster(const uint32_t clip[8],uint32_t texture_shift,const uint8_t*texture,uint32_t texture_bytes,uint8_t*framebuffer,uint32_t framebuffer_bytes,uint32_t stride);
/* Static descriptor+6 child after successful parent geometry.1 child,0 none,
   -1 invalid/unsupported sibling-chain mode. Preserves output unless1.
   Does not cover object callbacks or descriptor+24 sibling chains. */
__declspec(dllexport) int nfs_visibility_static_child_record(const uint8_t*,const uint8_t[16],unsigned,NFVisibilityRead,void*,const uint32_t*,uint8_t[16]);
/* Object dispatch22D8..2360: copy parent L/R into owned state; flag+0A bit10
   selects object+36 region.1 publishes record,0 other branch preserves record,
   -1 invalid preserves state/record. Does not select/sort objects. */
__declspec(dllexport) int nfs_visibility_object_region_prepare(uint8_t state[256],const uint8_t object[164],const uint8_t parent[16],uint8_t record[16]);
/* Composed sorted-object setup through2320, including recursive record branch.
   1 prepared,-1 invalid. Atomically publishes state, XYZ, branch (1 region,
   0 material path); record changes only for region. No projection or drawing. */
__declspec(dllexport) int nfs_visibility_object_branch_prepare(uint8_t state[256],const uint8_t object[164],const uint8_t parent[16],const uint32_t matrix[12],uint32_t xyz[3],unsigned*branch,uint8_t record[16]);
typedef struct {uint32_t region,head;} NFVisibilityObjectSource;
/* Owns ordered source roots and current collector. next returns1 starts a
   source,0 plan exhausted,-1 invalid/pending source. Caller retains shared
   pool/bitmap/sort globals across sources and handles sorted draw emission. */
typedef struct {NFVisibilityObjectSource sources[512];unsigned count,next,object_count;NFVisibilityObjectCollector collector;} NFVisibilityObjectDispatch;
__declspec(dllexport) int nfs_visibility_object_dispatch_begin(NFVisibilityObjectDispatch*,const NFVisibilityObjectSource*,unsigned,unsigned);
__declspec(dllexport) int nfs_visibility_object_dispatch_next(NFVisibilityObjectDispatch*,unsigned*);
/* Original54A0 source heads; caller supplies eligible region invocation.
   Flag8 follows descriptor+24 siblings, otherwise own region. FFFF heads skipped.
   Atomic ordered plan; no callbacks, object mutation, or pass gating. */
__declspec(dllexport) int nfs_visibility_object_sources(const uint8_t state[256],const uint8_t record[16],NFVisibilityRead,void*,NFVisibilityObjectSource*,unsigned,unsigned*);
/* Enclosing27F0 object-collection gate, after owned region setup.
   1 collect,0 skip,-1 invalid/unavailable. Does not collect or run callbacks. */
__declspec(dllexport) int nfs_visibility_region_object_gate(const uint8_t state[256],const uint8_t record[16],unsigned pass,NFVisibilityRead,void*,const uint32_t reciprocal[32768]);
/* Owned enclosing gate plus ordered source plan. 1 valid (including skipped),
   -1 unavailable/invalid/capacity. Publishes eligible and count atomically;
   skipped invocations emit zero sources. No callback or collection execution. */
__declspec(dllexport) int nfs_visibility_region_object_plan(const uint8_t state[256],const uint8_t record[16],unsigned pass,NFVisibilityRead,void*,const uint32_t reciprocal[32768],NFVisibilityObjectSource*,unsigned,unsigned*,unsigned*);
typedef struct {uint32_t kind,pass,mask;uint8_t record[16];} NFVisibilityRegionAction;
/* Ordered local recursion phases:1 surfaces,2 child invocation,3 collect/draw
   objects,4 deferred walls. Native geometry gates/deferred mask; caller runs
   each action depth-first. No leaf execution or callbacks. Atomic publication. */
__declspec(dllexport) int nfs_visibility_region_actions(const uint8_t state[256],const uint8_t record[16],unsigned pass,NFVisibilityRead,void*,const uint32_t reciprocal[32768],NFVisibilityRegionAction*,unsigned,unsigned*);
#endif
