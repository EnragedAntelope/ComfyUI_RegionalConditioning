# Development Context & Learnings

**Last Updated:** November 22, 2025
**ComfyUI Version:** 0.3.71
**Repository:** EnragedAntelope/ComfyUI_RegionalConditioning

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
- **Technology:** Binary masks created from drawn boxes
- **Critical Discovery:** Flux requires **0.7-0.85 mask strength** (NOT 1.0!)
  - Full strength (1.0) creates harsh, over-defined regions
  - Research shows 180-220 out of 255 (0.7-0.85 normalized) optimal
  - Implementation uses 0.8 as sweet spot
  - **Other Models:** Works well with mask-based models in general, user testing needed
- **Feathering:** 40-60px (5-8 latent pixels) gentle feathering improves blending
  - Tied to `soften_masks` toggle - user can disable for sharp edges
- **Region Limit (Flux):** Flux works best with 3-4 regions maximum (confirmed)
- **Region Limit (Chroma):** Likely 3-4 regions too since Chroma is Flux-based (UNTESTED - needs user confirmation)
- **Region Limit (SD3/SD3.5):** No known limit
- **CFG Guidance (Flux):** **Base Flux uses CFG 1.0 ONLY with NO negative prompt** (this is critical!)
  - Flux.1-dev/schnell are designed for CFG 1.0 baseline
  - Higher CFG values cause blur and artifacts
  - Do NOT use negative prompts with Base Flux
  - Dev variants may support higher CFG, but start with 1.0
- **Per-Region Strength (CRITICAL DISCOVERY - November 2025):**
  - **Each region needs its own strength control** - global strength doesn't work!
  - User testing showed: Both regions at 2.0 = car yes, giraffe no
  - Car at 2.0, giraffe at 4.0 = BOTH appear (red vehicle + giraffe)
  - **Implementation:** Added region1_strength, region2_strength, region3_strength, region4_strength inputs
  - **Recommended defaults:** 2.5, 3.5, 4.0, 4.0 (increasing strength for later regions)
  - **Why:** Background conditioning competes with regions - later regions need higher strength

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

#### JavaScript UI
- **Loading:** ComfyUI loads extensions from `/js/` folder **ONLY if `WEB_DIRECTORY` is exported in `__init__.py`**
  - **CRITICAL:** Must export `WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "js")`
  - Without this export, JavaScript files are completely ignored - canvas won't appear at all!
- **Canvas:** Shared drawing code between area-based and mask-based nodes
- **Grid:** 64px grid overlay helps users align to latent boundaries
- **Color Coding:** Each region gets unique color based on index/length ratio
- **Canvas Widget Critical Pattern:**
  - Must set `canvas.width` and `canvas.height` attributes (not just CSS styles)
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
