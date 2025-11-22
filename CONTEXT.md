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

#### Mask-Based Conditioning (Flux/Chroma/SD3)
- **Models:** Flux (all variants), Chroma (Chroma1-Radiance, etc.), SD3/SD3.5
- **Technology:** Binary masks created from drawn boxes
- **Critical Discovery:** Flux requires **0.7-0.85 mask strength** (NOT 1.0!)
  - Full strength (1.0) creates harsh, over-defined regions
  - Research shows 180-220 out of 255 (0.7-0.85 normalized) optimal
  - Implementation uses 0.8 as sweet spot
- **Feathering:** 40-60px (5-8 latent pixels) gentle feathering improves blending
- **Region Limit:** Flux works best with 3-4 regions maximum
- **CFG Guidance:** Increase to 5-7 (vs typical 3-5) for better regional control

#### CLIP Encoding (Inline Prompts)
- **Method:** `clip.tokenize(prompt)` → `clip.encode_from_tokens(tokens, return_pooled=True)`
- **Returns:** `(cond_tensor, pooled_output)`
- **Format:** Must wrap in list: `[[cond, {"pooled_output": pooled}]]`
- **Works:** Identical to external CLIPTextEncode nodes
- **Benefit:** Massive UX improvement - no external nodes needed!

#### JavaScript UI
- **Loading:** Modern ComfyUI auto-loads from `/js/` folder
- **Canvas:** Shared drawing code between area-based and mask-based nodes
- **Grid:** 64px grid overlay helps users align to latent boundaries
- **Color Coding:** Each region gets unique color based on index/length ratio

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
- **Theory:** Should work with standard CONDITIONING if it follows ComfyUI conventions
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
   - **Tooltip:** "✅ RECOMMENDED: Softer masks (0.8 strength + gentle edge blend) work better than harsh full-strength (1.0) masks. Confirmed for Flux. Try it first for Chroma/SD3, disable if you prefer sharper region edges."
   - **Node Description:** Dedicated "💡 IMPORTANT" section explaining when to keep ON vs turn OFF
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
   - **Clarification:** Node outputs CONDITIONING (connects to KSampler positive input)
   - **README:** Added detailed workflow diagram showing exact connections
   - **Impact:** Users understand the node flow correctly

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
- ✅ Good: "Mask-based node for Flux, Chroma, SD3"
- ❌ Bad: "Flux node" (implies Flux-only)
- ✅ Good: "Soften Masks (confirmed better for Flux, try for others)"
- ❌ Bad: "Flux Optimize" (confusing for Chroma/SD3 users)

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
- [ ] **WAN 2.2 Support:** Research single-frame generation conditioning
- [ ] **V3 Schema Migration:** When ComfyUI V3 becomes stable/mandatory
- [ ] **Complex Shapes:** Support for circular/polygonal regions (would require mask drawing UI)
- [ ] **Strength Gradients:** Gradual strength transitions between regions
- [ ] **Negative Regions:** Subtract conditioning from specific areas

---

## Known Issues & Workarounds

### Issue: Workflow Metadata Missing
- **Symptom:** "Workflow metadata missing" error on first run
- **Cause:** ComfyUI doesn't populate `extra_pnginfo` until workflow saved
- **Workaround:** Save workflow (Ctrl+S), reload page
- **Fix:** Fallback to sensible defaults (512x512 for SD, 1024x1024 for Flux)

### Issue: Canvas Not Updating
- **Symptom:** Boxes don't appear when drawn
- **Cause:** `app.graph._nodes` reference bug in old JavaScript
- **Fix:** Use `app.graph._nodes` consistently (fixed in modernization)

### Issue: Flux Regions Too Strong
- **Symptom:** Harsh boundaries, over-defined regions
- **Cause:** Mask strength set to 1.0 instead of 0.7-0.85
- **Fix:** RegionalPrompterFlux uses 0.8 by default with `flux_optimize=True`

---

## Testing Checklist

### Verified ✅
- [x] SD 1.5 area-based conditioning
- [x] SDXL area-based conditioning
- [x] Flux mask-based conditioning (with 0.8 strength)
- [x] Inline CLIP encoding matches external CLIPTextEncode
- [x] Canvas drawing and box visualization
- [x] Error handling with missing metadata
- [x] Bounds checking in MultiLatentComposite

### Needs Testing ⏳
- [ ] Chroma (Chroma1-Radiance) mask-based conditioning
- [ ] SD3 / SD3.5 mask-based conditioning
- [ ] Qwen-Image (generation model) compatibility
- [ ] Canvas scaling with different output resolutions
- [ ] Feathering effectiveness across different Flux models
- [ ] Region limit (>4 regions) quality degradation

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
- **Flux:** black-forest-labs/FLUX.1-dev, FLUX.1-schnell
- **Chroma:** GenerativeModels/Chroma1-Radiance
- **SD3:** StabilityAI/stable-diffusion-3-medium
- **Qwen-Image:** Qwen/Qwen-VL (needs confirmation)

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
