#ifndef NF_LAYER_SNAPSHOT_H
#define NF_LAYER_SNAPSHOT_H
#include <stdint.h>
#include <stddef.h>
typedef struct {uint32_t refresh,row;uint8_t registers[0x60];int32_t affine[6];} NFHardwareLayerHeader;
typedef struct {uint32_t refresh,row;uint8_t registers[0x60];int32_t affine[6];uint8_t vram[0x18000],palette[1024],oam[1024];} NFHardwareLayerRow;
typedef struct {uint32_t refresh,row;uint8_t registers[0x60];int32_t affine[6];uint8_t obj_vram[0x8000],palette[1024],oam[1024];} NFHudLayerRow;
typedef struct NFLayerSnapshot NFLayerSnapshot;
__declspec(dllexport) NFLayerSnapshot*nf_layer_snapshot_create(void);
/* Deep independent clone of a complete160-row snapshot; no borrowed pages. */
__declspec(dllexport) NFLayerSnapshot*nf_layer_snapshot_clone(const NFLayerSnapshot*);
__declspec(dllexport) void nf_layer_snapshot_destroy(NFLayerSnapshot*);
/* Only an unreferenced/expired owner may reset; retains allocated page storage. */
__declspec(dllexport) int nf_layer_snapshot_reset(NFLayerSnapshot*);
__declspec(dllexport) int nf_layer_snapshot_add(NFLayerSnapshot*,const NFHardwareLayerRow*);
/* Synchronously copies/deduplicates input parts; retains no borrowed pointers. Header is 128 bytes. */
__declspec(dllexport) int nf_layer_snapshot_add_parts(NFLayerSnapshot*,const void*,const void*,const void*,const void*);
/* Only trusted synchronous renderer write notifications may clear dirty bits.
   Row zero always copies all pages; verify checks every claimed clean page. */
__declspec(dllexport) int nf_layer_snapshot_add_dirty(NFLayerSnapshot*,const void*,const void*,const void*,const void*,uint32_t dirty,unsigned verify);
__declspec(dllexport) void nf_layer_snapshot_dirty_stats(uint64_t out[3]);
__declspec(dllexport) int nf_layer_snapshot_read(const NFLayerSnapshot*,unsigned,NFHardwareLayerRow*);
__declspec(dllexport) int nf_layer_snapshot_read_hud(const NFLayerSnapshot*,unsigned,NFHudLayerRow*);
/* Display-owned index-zero BGR555 for every row of one exact refresh.
   Complete snapshots only; output remains unchanged on failure. */
__declspec(dllexport) int nf_layer_snapshot_zero_colors(const NFLayerSnapshot*,uint32_t refresh,uint16_t out[160]);
/* All display-owned BG colors, row-major [160][256], complete exact refresh.
   Raw BGR555; no draw-time palette or live memory read. Atomic on failure. */
__declspec(dllexport) int nf_layer_snapshot_bg_palettes(const NFLayerSnapshot*,uint32_t refresh,uint16_t out[160][256]);
/* Conservative mode4 displayed-page equality; ignores OBJ data, rejects BG register/palette changes. */
__declspec(dllexport) int nf_layer_snapshot_display_page_equal(const NFLayerSnapshot*,const NFLayerSnapshot*);
__declspec(dllexport) int nf_layer_snapshot_display_page(const NFLayerSnapshot*,unsigned);
__declspec(dllexport) int nf_layer_snapshot_display_rows_equal(const NFLayerSnapshot*,const NFLayerSnapshot*,unsigned page,unsigned begin,unsigned end);
/* Actual retained allocation, including unused page capacity and metadata. */
__declspec(dllexport) size_t nf_layer_snapshot_bytes(const NFLayerSnapshot*);
__declspec(dllexport) int nf_layer_snapshot_refresh(const NFLayerSnapshot*,uint32_t*);
__declspec(dllexport) unsigned nf_layer_snapshot_pages(const NFLayerSnapshot*);
#endif
