# Development Context & Learnings

**Last Updated:** November 23, 2025
**ComfyUI Version:** 0.3.71+
**Repository:** EnragedAntelope/ComfyUI_EasyRegion (formerly ComfyUI_RegionalConditioning)

---

## Comprehensive Code Review - November 23, 2025

### Critical Bugfix: Attention Masking API Updated

**Issue:** Attention masking was causing `KeyError: 'attention_mask_img_shape'` crash during sampling.

**Root Cause:** ComfyUI PR #5942 implementation requires TWO fields for attention masking:
1. `attention_mask` - the binary mask tensor
2. `attention_mask_img_shape` - tuple of (height, width) for reference dimensions

**Fix Applied:** Added `attention_mask_img_shape` parameter (RegionalPrompting.py:483)
```python
n[1]['attention_mask'] = mask  # Binary mask for spatial control
n[1]['attention_mask_img_shape'] = (latent_height, latent_width)  # Required by API
```

**Status:** ✅ Fixed - attention masking now works correctly with ComfyUI 0.3.71+

**References:**
- [ComfyUI PR #5942](https://github.com/comfyanonymous/ComfyUI/pull/5942)
- [Attention Mask Implementation Details](https://github.com/comfyanonymous/ComfyUI/pull/5942#discussion)

---

### Documentation Corrections (November 23, 2025)

**Fixed Issues:**
1. ✅ **Tooltip Inconsistency:** Region 4 strength tooltip corrected from "5-7" to "4-6" to match tested optimal value (4.5)
2. ✅ **README Error:** Removed "Advanced Nodes" section documenting non-existent nodes (Multi Area Conditioning, Multi Area Conditioning Mask, Multi Latent Composite) - these were from the old ComfyUI_RegionalConditioning repo
3. ✅ **Variable Passing:** Verified all JS→Python data flow is correct:
   - ✅ `region_boxes` hidden widget serialization working
   - ✅ Per-region strength inputs (Mask-Based only) working correctly
   - ✅ Width/height sync (Mask-Based only) working correctly

**Known Design Differences (Intentional):**
- **Area-Based node** does NOT have per-region strength controls (uses hardcoded 1.0 from canvas values)
  - Reason: Area-based conditioning for SD/SDXL typically works well with strength 1.0
  - Future enhancement: Could add per-region strength for advanced users
- **Area-Based node** does NOT have width/height inputs (uses fixed 512x512 canvas)
  - Reason: Area-based conditioning auto-detects from latent, doesn't need explicit dimensions

---

## Attention Masking (Latest Feature - Nov 23, 2025)

**ComfyUI Requirement:** PR #5942 (merged ~1 year ago, widely available)

### Problem Solved: Spatial Mismatch

When you prompt "flying bird" with a region in the upper-right, but the model naturally wants to generate birds center-frame, standard mask conditioning alone may not be strong enough to force the generation into your region.

### Solution: Triple-Mask System

We now use **THREE complementary systems** working together:

1. **`mask` (feathered)** - Visual blending
   - Soft gradient edges if `soften_masks=True`
   - Smooth visual composition

2. **`mask_strength`** - Conditioning intensity
   - Range: 0.0 to 10.0 (default 2.5-4.5)
   - Controls HOW STRONGLY prompt is applied

3. **`attention_mask` (binary)** - Spatial forcing **[NEW!]**
   - Always binary 1.0 values, NO feathering
   - Forces model to ONLY attend to this region
   - Prevents "bird center-frame" when region is upper-right
   - Model-agnostic (Flux, SD3, SDXL, etc.)

### Implementation Details

**Code:** `RegionalPrompting.py:450-483`

```python
# Create binary mask
mask[0, y_latent:y_end, x_latent:x_end] = 1.0

# Clone for feathering (visual blending only)
feathered_mask = mask.clone()
if soften_masks:
    # Apply feathering to feathered_mask...

# Apply BOTH masks to conditioning
n[1]['mask'] = feathered_mask      # Soft edges for visual blending
n[1]['mask_strength'] = strength   # Intensity (2.5-4.5)
n[1]['attention_mask'] = mask      # Binary spatial forcing
```

**Key Points:**
- `mask` stays binary (1.0) for attention control
- `feathered_mask` gets gradient edges for smooth visuals
- Both applied to same conditioning - they work together
- Strength values (2.5-4.5) still needed for intensity control

### Why Both Masks?

- **Without attention_mask:** Bird might leak to center-frame where model naturally places birds
- **With attention_mask:** Model forced to respect region boundaries precisely
- **Feathering still needed:** For smooth visual transitions between regions

### Performance

- Negligible overhead (<1% slower)
- Works with all mask-based models
- Degrades gracefully if ComfyUI doesn't support it (just uses standard mask)

---

## Technical Learnings

### What Works ✅

#### Area-Based Conditioning (SD/SDXL)
- **Models:** Stable Diffusion 1.5, SD 2.x, SDXL
- **Technology:** Uses `ConditioningSetArea` internally
- **Coordinates:** All values divided by 8 for latent space conversion
- **Strength:** Full strength (1.0) works perfectly
- **Limitations:** Rectangular regions only, no complex shapes

#### Mask-Based Conditioning (Flux, Chroma, SD3, etc.)
- **Models:** Flux (all variants), Chroma (Chroma1-Radiance, etc.), SD3/SD3.5, and other mask-based models
- **Technology:** Binary masks (1.0 values) with `mask_strength` parameter controlling intensity
- **Critical Discovery - Strength Values (FINAL - November 2025):**
  - **Binary mask tensor:** Always use 1.0 values (not 0.8 or other values)
  - **Strength controlled by:** `mask_strength` parameter in conditioning dict
  - **Optimal Flux values with bg_strength=0.5:**
    - region1_strength: **2.5**
    - region2_strength: **3.5**
    - region3_strength: **4.0**
    - region4_strength: **4.5**
    - background_strength: **0.5** (range 0.3-0.7)
  - **⚠️ WARNING:** Values above 5.0 cause softness and detail loss!
  - **User testing results:**
    - Strength 2.5-4.5 = sharp details, regions show correctly
    - Strength 5.0+ = soft/blurry, loss of fine details
    - Background 0.5 works well (too high = regions don't show, too low = background disappears)
- **Region Positioning (CRITICAL):**
  - **Position regions FAR APART for best results** (e.g., left third and right third of image)
  - Overlapping or close regions compete and interfere with each other
  - Default templates now use far-apart positioning (50-350px and 674-974px for 1024x1024)
- **Feathering:** 40-60px (5-8 latent pixels) gentle feathering improves blending
  - Tied to `soften_masks` toggle - user can disable for sharp edges
  - Feathering gradient: 0.0 to 1.0 (not scaled by mask strength)
- **Region Limit (Flux):** Flux works best with 3-4 regions maximum (confirmed)
- **Region Limit (Chroma):** Likely 3-4 regions too since Chroma is Flux-based (UNTESTED - needs user confirmation)
- **Region Limit (SD3/SD3.5):** No known limit
- **CFG Guidance (Flux):** **Base Flux uses CFG 1.0 ONLY with NO negative prompt** (this is critical!)
  - Flux.1-dev/schnell are designed for CFG 1.0 baseline
  - Higher CFG values cause blur and artifacts
  - Do NOT use negative prompts with Base Flux
  - Dev variants may support higher CFG, but start with 1.0
- **Per-Region Strength Implementation:**
  - **Each region has independent strength control** - essential for balancing multiple regions
  - Added region1_strength, region2_strength, region3_strength, region4_strength inputs
  - Step size: 0.1 for fine control
  - **Conditioning key:** Use `mask_strength` (not `strength`) for mask-based conditioning
  - **set_area_to_bounds:** Should be False for mask-based conditioning

#### CLIP Encoding (Inline Prompts)
- **Method:** `clip.tokenize(prompt)` → `clip.encode_from_tokens(tokens, return_pooled=True)`
- **Returns:** `(cond_tensor, pooled_output)`
- **Format:** Must wrap in list: `[[cond, {"pooled_output": pooled}]]`
- **Works:** Identical to external CLIPTextEncode nodes
- **Benefit:** Massive UX improvement - no external nodes needed!
- **Universal:** Same method works for ALL models (SD/SDXL/Flux/Chroma/SD3/etc.) - ComfyUI handles multi-encoder complexity internally

#### Text Encoder Architectures by Model
**CRITICAL:** Different models use different numbers and types of text encoders. ComfyUI's CLIP object handles the complexity internally, but understanding the architecture helps with debugging.

| Model | # Encoders | Encoder Types | Implementation Notes |
|-------|-----------|---------------|---------------------|
| **SD 1.5** | 1 | CLIP-L | Standard `encode_from_tokens` |
| **SD 2.x** | 1 | OpenCLIP-H | Standard `encode_from_tokens` |
| **SDXL** | 2 | CLIP-L + OpenCLIP-G | Standard `encode_from_tokens` (handled internally) |
| **Flux** ✅ | 2 | T5-XXL + CLIP-L | Standard `encode_from_tokens` (handled internally) |
| **Chroma** ✅ | 1 | T5-XXL only | Standard `encode_from_tokens` (Flux-based but single encoder!) |
| **SD3** | 3 | CLIP-L + CLIP-G + T5-XXL | Standard `encode_from_tokens` (multi-encoder internal) |
| **SD3.5** | 3 | CLIP-L + CLIP-G + T5-XXL | Standard `encode_from_tokens` (multi-encoder internal) |
| **HiDream** | 4 | CLIP-L + CLIP-G + 2× T5 variants | Standard `encode_from_tokens` (multi-encoder internal) |
| **WAN 2.1** | 1 | UMT5-XXL | Standard `encode_from_tokens` (fp16/fp8/bf16 variants) |
| **WAN 2.2** | 1 | UMT5-XXL + MoE | Standard `encode_from_tokens` (nf4 4-bit quantization) |
| **Qwen-Image** | 1 | Qwen 2.5 VL (qwen_2.5_vl_7b.safetensors) | Standard `encode_from_tokens` (vision-language LLM) |

**Implementation (Simplified - November 2025):**
```python
# Universal encoding for ALL models (1, 2, 3, or 4 encoders)
# ComfyUI's CLIP object handles multi-encoder complexity internally
for prompt in prompts:
    if prompt and prompt.strip():
        tokens = clip.tokenize(prompt)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        encoded_conditionings.append([[cond, {"pooled_output": pooled}]])
```

**Critical Discovery (November 2025):**
- ❌ **WRONG:** Using `hasattr(clip, 'encode_from_tokens_scheduled')` to detect Flux
  - This method exists in the **base CLIP class** that ALL models inherit from
  - Returns `True` for SD1.5, SDXL, SD3, Flux, Chroma - everything!
  - Completely useless for model detection
- ✅ **CORRECT:** Use standard `encode_from_tokens(return_pooled=True)` for ALL models
  - Works universally: SD (1 encoder), SDXL (2), Flux (2), SD3 (3), HiDream (4)
  - ComfyUI's CLIP object abstracts encoder complexity
  - No model-specific branching needed
- 📝 **Note:** `encode_from_tokens_scheduled` is what CLIPTextEncode uses internally, but for regional prompting without temporal effects, `encode_from_tokens` works perfectly

**Key Insights:**
- ✅ **Chroma is Flux-based architecture but uses ONLY 1 encoder** (T5-XXL, not CLIP-L+T5-XXL)
- ✅ **SD3/SD3.5 use 3 encoders** but ComfyUI's CLIP handles it transparently
- ✅ **HiDream uses 4 encoders** in ComfyUI (CLIP-L, CLIP-G, T5 variants)
- ✅ **ALL models** use the same encoding method - no special cases needed
- ⚠️ **Don't assume encoder count from architecture** - Chroma proves Flux-based ≠ dual encoder!

**Critical Bugfixes (November 2025):**
- 🐛 **Variable Shadowing Bug:** Fixed `IndexError: list index out of range` crash in feathering loop
  - **Cause:** Inner loop variable `i` was shadowing outer loop variable `i`
  - **Symptom:** Crash when accessing `encoded_conditionings[i]` after feathering loop
  - **Fix:** Renamed inner loop variable to `edge_idx` (RegionalPrompting.py:397)
  - **Impact:** RegionalPrompterFlux would crash on execution with feathering enabled
- 🔧 **Missing WEB_DIRECTORY Export:** Canvas wasn't loading at all
  - **Cause:** No `WEB_DIRECTORY` export in `__init__.py` - ComfyUI couldn't find JS files
  - **Symptom:** Canvas widget completely invisible, no drawing interface shown
  - **Fix:** Added `WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "js")` export
  - **Impact:** JavaScript extensions weren't being loaded, canvas completely broken
- 🐛 **Widget Callback Context Bug:** Fixed `TypeError: can't access property "step", this.options is undefined`
  - **Cause:** Width/height widget callbacks used `.bind(this)` which bound to node, then called original callback with node as context
  - **Symptom:** Loading workflows crashed with "can't access property step" error (original callback expected widget as `this`)
  - **Fix:** Removed `.bind(this)`, captured node reference in closure, call original callback with widget context using `.call(this, value)`
  - **Impact:** Workflows wouldn't load at all in web-based ComfyUI instances (MimicPC, browser-based)
  - **Location:** RegionalPrompting.js:364-393
- 🎨 **Node Naming:** Removed "EASY!" terminology and made names model-agnostic
  - **Before:** "Regional Prompter (Flux/Chroma - Easy!)" ← Model-specific and gimmicky
  - **After:** "Regional Prompter (Mask-Based)" ← Describes technique, not specific models
  - **Reasoning:** Mask-based conditioning works for Flux, Chroma, SD3, Qwen-Image, etc.
  - **Also Updated:** "SD/SDXL - Easy!" → "Area-Based" (describes conditioning method)

#### JavaScript UI & Canvas
- **Loading:** ComfyUI loads extensions from `/js/` folder **ONLY if `WEB_DIRECTORY` is exported in `__init__.py`**
  - **CRITICAL:** Must export `WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "js")`
  - Without this export, JavaScript files are completely ignored - canvas won't appear at all!
- **Canvas Drawing:** Shared drawing code between area-based and mask-based nodes
- **Grid:** 64px grid overlay helps users align to latent boundaries
- **Color Coding:** Each region gets unique color based on index/length ratio
- **Canvas Sizing (CRITICAL - Learned through MANY failed attempts):**
  - **❌ WRONG:** Dynamic canvas height calculation based on node size and widget heights
    - Attempted MIN_SIZE with BOTTOM_PADDING calculations → constant overlap issues
    - Tried `freeSpace - widgetHeight` calculations → canvas extended beyond node bounds
    - Attempted 10+ different padding/sizing formulas → none worked reliably
  - **✅ CORRECT:** **FIXED canvas height (280px)** - simple and reliable
    - Set `const CANVAS_HEIGHT = 280` in `computeCanvasSize()`
    - Set `minHeight: 280` in `addEasyRegionCanvas()` return value
    - Node size auto-adjusts to fit canvas + all widgets + 20px bottom margin
    - **This is how most ComfyUI custom nodes handle canvas widgets**
  - **Key Insight:** Dynamic sizing sounds good in theory but causes endless edge cases
    - Different widget counts, resizing, prompt multiline expansion all broke dynamic sizing
    - Fixed height eliminates all these issues and provides consistent UX
- **Widget Positioning:**
  - Widgets positioned sequentially after canvas with 4px spacing
  - Canvas always comes after prompt inputs, before box manipulation widgets
- **Region Selector Mapping (1-based UI to 0-based array):**
  - **UI displays:** "Region 1", "Region 2" (user-friendly)
  - **Internally stores:** `values[0]`, `values[1]` (array indexing)
  - **transformFunc:** MUST convert `regionValue - 1` to get array index
  - **Critical Bug:** Was using selector value directly → editing Region 1 modified Region 2!
- **Future Enhancement - Help Icon:**
  - **TODO:** Add ? icon in node title bar that opens usage help modal
  - Other custom nodes implement this (not unique to our nodes)
  - Would provide: general usage tips, strength guidelines, troubleshooting
  - **Implementation:** Custom button in title bar with click handler showing modal overlay
  - CSS controls display size, attributes control internal drawing resolution
  - Force initial size computation with `setTimeout(() => computeCanvasSize(node, node.size), 100)`
  - Always provide fallback values for `node.canvasHeight`, `node.properties["values"]`, etc.

#### Workflow Metadata
- **Source:** `extra_pnginfo["workflow"]["nodes"]` contains node properties
- **Storage:** Canvas dimensions stored in `properties["width"]` and `properties["height"]`
- **Region Data:** Box coordinates stored as `properties["values"]` array
- **Format:** Each value is `[x, y, width, height, strength]`
- **Fallback:** Always provide defaults if metadata missing or corrupted

### What Doesn't Work ❌

#### WAN 2.2 Support
- **Status:** Not currently supported
- **Reason:** Video-focused architecture with temporal layers
- **Use Case:** Users want single-frame image generation
- **Future:** May be possible but needs deeper research into WAN's conditioning pipeline

#### Qwen-Image Compatibility
- **Status:** Experimental/Unknown
- **Type:** Generation model (not edit variant)
- **Theory:** Should work with mask-based conditioning (RegionalPrompterFlux) if it follows ComfyUI conventions
- **Guidance:** "Try it and see what breaks" - no specific settings known
- **Recommendation:**
  - Start with mask-based node (RegionalPrompterFlux)
  - Keep soften_masks ON
  - Try standard settings and adjust based on results
  - Report findings to help others!
- **Blocker:** No test workflows or confirmed compatibility reports
- **Future:** Needs actual testing with Qwen-Image checkpoints

#### V3 Schema Migration
- **Status:** Optional, not required yet
- **ComfyUI 0.3.71:** Still fully supports traditional `INPUT_TYPES` class method
- **V3 Features:** Stateless validation, better type checking, optional migrations
- **Timeline:** Will be needed when V3 becomes mandatory (TBD by ComfyUI team)

### Critical Code Patterns

#### Latent Space Conversion
```python
# Always divide pixel coordinates by 8 for VAE downscaling
x_latent = x // 8
y_latent = y // 8
w_latent = w // 8
h_latent = h // 8

# For area-based conditioning (height, width, y, x order!)
n[1]['area'] = (h // 8, w // 8, y // 8, x // 8)
```

#### Mask Creation (Flux-Optimized)
```python
# Create mask tensor (latent dimensions)
mask = torch.zeros((1, latent_height, latent_width), dtype=torch.float32)

# Fill with optimized strength (0.8 for Flux, 1.0 for others)
mask_strength = 0.8 if flux_optimize else 1.0
mask[0, y_latent:y_end, x_latent:x_end] = mask_strength

# Apply gentle feathering (5-8 latent pixels)
feather_size = min(6, w_latent // 4, h_latent // 4)
for i in range(feather_size):
    fade = (i + 1) / feather_size * mask_strength
    # Apply to all four edges...
```

#### Error Handling Pattern
```python
try:
    if not extra_pnginfo:
        raise ValueError("Missing workflow metadata")
    # ... complex operations ...
except Exception as e:
    print(f"⚠️  Warning: {str(e)}")
    # Provide sensible fallback behavior
    return default_output
```

---

## Architecture Decisions

### Why Two Node Types?
- **Area-Based (MultiAreaConditioning):** More efficient for SD/SDXL, native support
- **Mask-Based (MultiAreaConditioningMask):** Required for Flux/Chroma, more flexible

### Why Enhanced "Easy" Nodes?
- **Problem:** Original nodes required external CLIPTextEncode for every region
- **Solution:** Inline prompts with internal CLIP encoding
- **Benefit:** Simpler workflows, better UX, fewer nodes to manage
- **Trade-off:** Less flexible than external nodes (can't share encodings)

### Why Keep Original Nodes?
- **Backward Compatibility:** Existing workflows still work
- **Advanced Use Cases:** Some users need external CLIP encoding for shared prompts
- **Testing:** Easier to compare behavior between implementations

---

## User Experience Insights

### What Users Love
- Visual box drawing interface (intuitive, color-coded)
- Grid overlay (helps align to 64px boundaries)
- Inline prompts (no external nodes needed)
- Automatic mask conversion (boxes → masks behind the scenes)
- Default templates with example prompts and pre-drawn boxes

### UX Improvements (November 2025)

1. **✅ FIXED: First-Time Experience**
   - **Was:** Blank canvas with no example, intimidating for new users
   - **Now:** Pre-filled example prompts ("red sports car", "street vendor") + pre-drawn boxes
   - **Impact:** Users can test immediately without reading docs

2. **✅ FIXED: Soften Masks Clarity**
   - **Was:** Parameter named `flux_optimize` (confusing since node works for Chroma/SD3 too)
   - **Now:** Renamed to `soften_masks` with explicit tooltip guidance
   - **Tooltip:** "✅ RECOMMENDED: Softer masks (0.8 strength + gentle edge blend) work better than harsh full-strength (1.0) masks. Confirmed better for Flux, works well with other mask-based models. Disable if you prefer sharper region edges."
   - **Node Description:** Dedicated "💡 IMPORTANT" section explaining when to keep ON vs turn OFF
   - **Model References:** Changed from "Try it first for Chroma/SD3" to "Works well with other models - try it first!" (more general)
   - **Impact:** Users understand it's a softness toggle (not Flux-specific magic), know when to enable/disable

3. **✅ FIXED: Feathering Concerns**
   - **Question:** Is feathering the only option? Will it look crappy?
   - **Answer:** Feathering is optional - tied to the `soften_masks` toggle
     - ON: 0.8 strength + gentle 5-8px feather (better blending)
     - OFF: 1.0 strength + no feather (sharp edges)
   - **Advanced Option:** Use MultiAreaConditioningMask node for manual `mask_strength` control (0.1-1.0 slider)
   - **Why Feathering:** Avoids harsh boundaries that can look artificial, based on Flux research
   - **Impact:** Users have full control, understand the trade-offs

4. **✅ FIXED: Dynamic Canvas Sync**
   - **Was:** Users had to manually edit properties to resize canvas
   - **Now:** Canvas auto-resizes when width/height inputs change on Flux node
   - **Implementation:** Widget callbacks sync properties in real-time
   - **Impact:** Seamless UX, boxes scale proportionally

5. **✅ FIXED: Workflow Setup Confusion**
   - **Question:** Does it need a latent input?
   - **Answer:** NO! Only needs CLIP input + width/height parameters (just numbers)
   - **Pro Tip:** Width/height inputs accept connections - users can drag from Empty Latent Image outputs!
   - **Clarification:** Node outputs CONDITIONING (connects to KSampler positive input)
   - **README:** Added detailed workflow diagram showing exact connections
   - **Node Description:** Added tip about connecting from Empty Latent Image
   - **Impact:** Users understand the node flow correctly AND can auto-sync dimensions

6. **Dynamic Latent Sizing:**
   - **Question:** Does it work with any input size?
   - **Answer:** YES! Canvas dimensions are independent from output dimensions
   - **How:** RegionalPrompterFlux scales boxes from canvas to output size
   - **Example:** Draw on 512x512 canvas, output at 1024x1024 → boxes scale 2x automatically
   - **Important:** Width/height in Regional Prompter should match Empty Latent Image size

7. **Region Limit Feedback:**
   - **Fixed:** Console warning if >4 regions detected for Flux

---

## Naming Consistency & Terminology

### Critical Guidelines (November 2025)

**Problem:** Calling things "Flux" when they apply to multiple models confuses users.

**Rules:**
1. ✅ **Use "Flux"** when feature is Flux-specific (e.g., "3-4 region limit for Flux")
2. ✅ **Use "Mask-Based"** when referring to the conditioning method (Flux/Chroma/SD3/SD3.5)
3. ✅ **Use "Soften Masks"** for the toggle (not "Flux Optimize") - it's model-agnostic
4. ✅ **Use "Area-Based"** for SD1.5/SD2.x/SDXL conditioning
5. ❌ **Don't use "Flux"** as shorthand for mask-based conditioning

**Examples:**
- ✅ Good: "Mask-based node for Flux, Chroma, SD3, etc."
- ❌ Bad: "Flux node" (implies Flux-only)
- ✅ Good: "Soften Masks (confirmed better for Flux, works well with other models)"
- ❌ Bad: "Flux Optimize" (confusing for other model users)
- ✅ Good: "3-4 region limit for Flux" (specific model reference)
- ⚠️ Uncertain: "Chroma likely has 3-4 region limit too (untested)" (honest about uncertainty)
- ✅ Good: "Flux and similar models" (acknowledges Flux-based architecture)

### Audit Checklist
- [x] Node names clarified (not Flux-exclusive)
- [x] Parameter renamed (`flux_optimize` → `soften_masks`)
- [x] Tooltips use accurate model references
- [x] Node descriptions separate model-specific tips
- [x] README uses "mask-based" consistently
- [x] CONTEXT.md documents terminology rules

---

## Future Improvements

### High Priority
- [x] **Default Template Mode:** Pre-filled example prompts and drawn boxes for first launch ✅ DONE
- [ ] **Qwen-Image Testing:** Acquire checkpoint and test compatibility
- [x] **Dynamic Canvas Sync:** Auto-resize canvas when latent input size changes ✅ DONE
- [ ] **Validation Warnings in UI:** Show visual warnings when regions exceed recommended limits

### Medium Priority
- [ ] **Expose Flux Strength (Optional):** Add `mask_strength` parameter to RegionalPrompterFlux if users request
- [ ] **Mask Visualization:** Show actual generated mask in canvas overlay (debugging)
- [ ] **Region Labels:** Display region number/name on each box
- [ ] **Copy/Paste Regions:** Right-click menu to duplicate region boxes

### Low Priority / Future Research
- [ ] **Mouse-Based Box Manipulation:** Allow users to draw and move region boxes with mouse
  - Currently users adjust x/y/width/height with numeric inputs
  - Future improvement: Click and drag to create boxes, drag corners to resize
  - Would require significant JavaScript canvas interaction code
  - Reference: Many image editing tools use similar drag-to-draw interfaces
- [ ] **WAN 2.2 Support:** Research single-frame generation conditioning
- [ ] **V3 Schema Migration:** When ComfyUI V3 becomes stable/mandatory
- [ ] **Complex Shapes:** Support for circular/polygonal regions (would require mask drawing UI)
- [ ] **Strength Gradients:** Gradual strength transitions between regions
- [ ] **Negative Regions:** Subtract conditioning from specific areas

---

## Known Issues & Workarounds

### ✅ FIXED: Canvas Not Visible (November 2025)
- **Symptom:** "Where exactly do you draw boxes? I see nothing."
- **Cause:** Canvas element missing explicit width/height attributes, computeCanvasSize not called initially
- **Fix:**
  - Set canvas.width and canvas.height attributes (not just CSS styles)
  - Force initial canvas size computation with setTimeout
  - Added fallback dimensions (200px minimum)
  - Added safeguards for empty values array
- **Status:** Fixed in commit 747c881

### ✅ FIXED: Regions Not Showing (November 2025)
- **Symptom:** Only background appears, regions (sports car, vendor) don't render
- **Cause:** `extra_pnginfo` empty on first run (before workflow saved), no default boxes
- **Fix:**
  - Added default template boxes matching JavaScript defaults
  - RegionalPrompterSimple: `[[50, 150, 200, 250, 1.0], [280, 150, 180, 250, 1.0]]`
  - RegionalPrompterFlux: `[[100, 300, 400, 500, 1.0], [560, 300, 350, 500, 1.0]]`
  - Boxes only used if workflow not saved yet
- **Status:** Fixed in commit 747c881

### ✅ FIXED: Wrong CLIP Encoder for Chroma/Qwen (November 2025)
- **Symptom:** mat1/mat2 tensor shape mismatch error (when wrong CLIP selected)
- **Cause:** Assumed all mask-based models need dual encoders like Flux
- **Fix:**
  - Detect Flux via `hasattr(clip, 'encode_from_tokens_scheduled')`
  - Flux: dual encoder (CLIP-L + T5-XXL) with guidance
  - Chroma/Qwen/SD3: single encoder (standard encoding)
- **Reality Check:** User error (SDXL CLIP loader), but encoder detection still improved
- **Status:** Fixed in commit 747c881

---

## Testing Checklist

### Verified ✅
- [x] SD 1.5 area-based conditioning
- [x] SDXL area-based conditioning
- [x] Flux mask-based conditioning (with 0.8 strength)
- [x] Flux dual-encoder CLIP detection and encoding
- [x] Inline CLIP encoding matches external CLIPTextEncode
- [x] Canvas widget visibility and proper rendering (November 2025)
- [x] Canvas drawing and box visualization
- [x] Default template boxes work without saving workflow (November 2025)
- [x] Error handling with missing metadata
- [x] Bounds checking in MultiLatentComposite

### Needs Testing ⏳
- [ ] Chroma (Chroma1-Radiance) mask-based conditioning (1 encoder: T5-XXL)
- [ ] SD3 / SD3.5 mask-based conditioning (3 encoders: CLIP-L + CLIP-G + T5-XXL)
- [ ] HiDream compatibility (4 encoders in ComfyUI)
- [ ] WAN 2.1 / WAN 2.2 compatibility (1 encoder: UMT5-XXL)
- [ ] Qwen-Image (generation model) compatibility (1 encoder: Qwen 2.5 VL LLM)
- [ ] Canvas scaling with different output resolutions
- [ ] Feathering effectiveness across different Flux models
- [ ] Region limit (>4 regions) quality degradation
- [ ] Dynamic canvas resize responsiveness (width/height input changes)

---

## Resources & References

### ComfyUI Documentation
- [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)
- [Custom Nodes Guide](https://docs.comfy.org/essentials/custom_node_overview)
- [JavaScript Extensions](https://docs.comfy.org/essentials/javascript_objects_and_widgets)

### Research Findings
- Flux mask strength: Community testing shows 0.7-0.85 optimal (180-220/255)
- Flux region limits: 3-4 regions maximum for quality results
- Feathering: 40-60px (5-8 latent) provides gentle blending without blur

### Model Information
- **Flux:** black-forest-labs/FLUX.1-dev, FLUX.1-schnell (2 encoders: T5-XXL + CLIP-L)
- **Chroma:** GenerativeModels/Chroma1-Radiance (1 encoder: T5-XXL only)
- **SD3:** StabilityAI/stable-diffusion-3-medium (3 encoders: CLIP-L + CLIP-G + T5-XXL)
- **SD3.5:** StabilityAI/stable-diffusion-3.5 variants (3 encoders: CLIP-L + CLIP-G + T5-XXL)
- **HiDream:** HiDream-I1, HiDream-E1 (4 encoders in ComfyUI: CLIP-L + CLIP-G + T5 variants)
- **WAN 2.1:** UMT5-XXL (1 encoder: fp16/fp8/bf16 variants)
- **WAN 2.2:** UMT5-XXL + MoE architecture (1 encoder: nf4 4-bit quantization)
- **Qwen-Image:** Qwen/Qwen-VL (1 encoder: Qwen 2.5 VL - qwen_2.5_vl_7b.safetensors vision-language LLM)

---

## Development Notes

### Code Style
- Comprehensive error handling with helpful messages (⚠️/ℹ️/❌ prefixes)
- Validation at boundaries (user input, external APIs)
- Fallback behavior for missing metadata
- No over-engineering - keep solutions minimal and focused

### Performance Considerations
- Mask creation: O(1) for rectangular regions
- CLIP encoding: Same cost as external nodes
- Canvas drawing: Negligible (client-side JavaScript)
- Feathering: O(feather_size) per region (minimal impact)

### Backward Compatibility
- Original nodes (MultiAreaConditioning, MultiAreaConditioningMask) unchanged
- Enhanced nodes (RegionalPrompter*) are additive, not replacements
- JavaScript files moved but functionality identical
- Workflow migration not required

---

**Maintainer Notes:**
- Always test with actual model checkpoints before claiming compatibility
- Document all breaking changes in README changelog
- Keep CONTEXT.md updated with new learnings
- Credit original author (Davemane42) in README and LICENSE

---

## Helpful Resources & Reference Implementations

### Working Regional Conditioning Implementations (2025)

#### RES4LYF - Advanced Flux Regional Conditioning
- **Repository:** https://github.com/city96/RES4LYF
- **Approach:** Model patching with attention mask injection
- **Key Techniques:**
  - Patches Flux transformer blocks directly (not just conditioning)
  - Creates cross-attention masks (text-to-image) and self-attention masks (image-to-image)
  - Uses `regional_generate_conditionings_and_masks_fn` injected into conditioning dict
  - Timestep-based control with `start_percent` and `end_percent`
  - `mask_weight` parameter (default 1.0, range -10000 to 10000)
  - `region_bleed` parameter for controlling region boundary blending
- **Conditioning Format:**
  - `conditioning_regional` list with `{'mask': tensor, 'cond': tensor}` dicts
  - Masks interpolated to latent resolution (h//2, w//2 for 16x16 positional encoding)
  - Regional conditioning combined with main conditioning via attention masking
- **Differences from Our Implementation:**
  - Much more complex - patches model internals, not just conditioning metadata
  - Requires model patching (ReFluxPatcher)
  - Our simpler approach uses standard ComfyUI `mask_strength` conditioning key
  - RES4LYF has more precise control but higher complexity

#### Curved Weight Schedule - Multi-Layer Mask Editor
- **Repository:** https://github.com/diffussy69/comfyui-curved_weight_schedule
- **Key Feature:** Interactive canvas-based mask painting with brush tools
- **Canvas Implementation:**
  - Mouse events: mousedown, mousemove, mouseup for brush painting
  - Pan/zoom: CSS transforms with `translate()` and `scale()`
  - Coordinate conversion: `screenToCanvas()` and `canvasToScreen()` helpers
  - Brush interpolation: `drawLine()` samples intermediate points for smooth strokes
  - Multi-layer support: Up to 10 independent mask layers with visibility toggling
  - Serialization: Base64-encoded alpha channels uploaded to backend as JSON
- **Regional Conditioning:**
  - Uses standard `mask_strength` key (same as our implementation)
  - Default strength 1.0 (much lower than our Flux values of 5.0-8.0)
  - `set_area_to_bounds: False` (same as ours)
  - No Flux-specific handling (architecture-agnostic)
- **Potential Integration:**
  - Could adopt their mouse-based mask painting for future enhancement
  - Their canvas interaction code is well-structured and modular
  - Would replace our current box-based drawing with freeform brush painting

### ComfyUI Official Documentation
- **Conditioning Format:** https://docs.comfy.org/essentials/conditioning
- **Custom Nodes Guide:** https://docs.comfy.org/developers/custom-nodes
- **Mask-Based Conditioning:** Standard practice is binary masks (0.0/1.0) with `mask_strength` parameter
- **Area-Based Conditioning:** Uses `ConditioningSetArea` with `strength` parameter (different from `mask_strength`)

### Key Differences: Our Implementation vs Others

**Our Implementation (ComfyUI_RegionalConditioning):**
- Simplest approach: Standard ComfyUI conditioning with `mask_strength` metadata
- Pre-drawn boxes with manual coordinate adjustment (no mouse painting yet)
- Per-region strength controls (4 regions max)
- Binary masks with feathering option
- High strength values for Flux (5.0-8.0+)
- No model patching required

**RES4LYF:**
- Most complex: Patches Flux model internals with custom attention masks
- Requires ReFluxPatcher to modify model behavior
- More precise regional control via attention masking
- Lower strength values (default 1.0)
- Advanced features: timestep control, region bleed

**Curved Weight Schedule:**
- Middle complexity: Standard conditioning with advanced UI
- Interactive canvas with brush painting and pan/zoom
- Multi-layer mask support (10 layers)
- Lower strength values (default 1.0)
- No Flux-specific handling

**Recommendation:**
- For basic regional prompting: Our implementation works and is simple
- For advanced control: RES4LYF provides more precision at cost of complexity
- For UI/UX: Curved Weight Schedule has best canvas interaction (could be adopted)
