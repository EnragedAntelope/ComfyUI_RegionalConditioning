# Regional Conditioning for ComfyUI

**The simplest way to control exactly where things appear in your images.**

Draw boxes on a canvas, type what you want in each region, and generate! Perfect for precise composition control in Stable Diffusion, SDXL, Flux, and Chroma.

---

## 🚀 Quick Start (60 seconds)

### For Flux / Chroma (Modern Models)

1. Load your Flux/Chroma checkpoint
2. Add the **🎨 Regional Prompter (Flux/Chroma - Easy!)** node
3. Connect CLIP from your checkpoint to the node
4. Type in the background prompt: `"photo of a city street"`
5. Draw a box on the canvas where you want something specific
6. Type in Region 1 prompt: `"red sports car"`
7. Draw another box for something else
8. Type in Region 2 prompt: `"street vendor"`
9. Connect the conditioning output to your sampler
10. Generate! 🎉

**That's it!** No external nodes, no complex wiring. Just prompts and boxes.

### For SDXL / Stable Diffusion

Same steps, but use **🎨 Regional Prompter (SD/SDXL - Easy!)** instead.

---

## ✨ Why Use This?

**Without Regional Conditioning:**
- "A tiger and a berry bush in front of mountains"
- → AI puts them wherever it wants (usually random placement)

**With Regional Conditioning:**
- Background: "Mountains"
- Box 1 (left side): "Tiger"
- Box 2 (right side): "Berry bush"
- → AI puts them **exactly where you drew the boxes**

**Perfect for:**
- Character positioning in scenes
- Multi-subject compositions
- Product photography layouts
- Architectural visualization
- Comic/storyboard panels

---

## 📦 Installation

### Method 1: ComfyUI Manager (Easiest)
1. Open ComfyUI Manager
2. Search for "Regional Conditioning"
3. Click Install
4. Restart ComfyUI

### Method 2: Manual
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/EnragedAntelope/ComfyUI_RegionalConditioning
# Restart ComfyUI
```

---

## 🎨 Which Node Should I Use?

### 🌟 RECOMMENDED: Enhanced Easy Nodes

These are the **easiest** way to use regional conditioning:

#### **🎨 Regional Prompter (Flux/Chroma - Easy!)**
- ✅ For: Flux, Chroma, SD3, SD3.5
- ✅ Type prompts directly in the node
- ✅ Optimized for Flux (perfect mask strength and blending)
- ✅ Just connect CLIP and go!

#### **🎨 Regional Prompter (SD/SDXL - Easy!)**
- ✅ For: Stable Diffusion 1.5, SD 2.x, SDXL
- ✅ Type prompts directly in the node
- ✅ Same simple workflow
- ✅ Perfect for traditional SD models

**Use these unless you have a specific reason not to.**

### 🔧 Advanced Nodes (For Power Users)

If you need more control or want to share CLIP encodings across multiple nodes:

- **Multi Area Conditioning (SD/SDXL - Advanced)** - Area-based for traditional SD
- **Multi Area Conditioning (Flux/Chroma - Advanced)** - Mask-based for modern models

These require external CLIP Text Encode nodes but offer more flexibility.

---

## 🎯 Model Compatibility

| Model Type | Node to Use | Status |
|------------|-------------|--------|
| **Stable Diffusion 1.5** | 🎨 Regional Prompter (SD/SDXL) | ✅ Fully Supported |
| **Stable Diffusion 2.x** | 🎨 Regional Prompter (SD/SDXL) | ✅ Fully Supported |
| **SDXL** | 🎨 Regional Prompter (SD/SDXL) | ✅ Fully Supported |
| **Flux** (all variants) | 🎨 Regional Prompter (Flux/Chroma) | ✅ Fully Supported & Optimized |
| **Chroma** (Radiance, etc.) | 🎨 Regional Prompter (Flux/Chroma) | ✅ Fully Supported |
| **SD3 / SD3.5** | 🎨 Regional Prompter (Flux/Chroma) | ✅ Fully Supported |
| **Qwen-Image** | 🎨 Regional Prompter (Flux/Chroma) | 🟡 Experimental (untested) |

---

## 💡 How to Use (Detailed)

### Understanding the Canvas

When you add a Regional Prompter node, you'll see:
- **A canvas** (black rectangle) - This is your drawing area
- **Prompt boxes** (text inputs) - Background + up to 4 regions
- **Drawing controls** (below canvas) - Position and size your boxes

### Drawing Your First Region

1. **Start with background prompt:**
   - Type: `"photo of a sunny beach"`
   - This applies to the whole image

2. **Add your first region:**
   - In Region 1 prompt, type: `"woman in red dress"`
   - Below the canvas, find the controls for Region 1
   - Set: `x=100, y=200, width=300, height=400`
   - You'll see a colored box appear on the canvas!

3. **Adjust the box visually:**
   - Change the `index` dropdown to select which region to edit
   - Each region gets a unique color
   - The 64px grid helps you align precisely

4. **Add more regions:**
   - Type in Region 2 prompt: `"beach umbrella"`
   - Adjust x/y/width/height to position it
   - Repeat for up to 4 regions total

5. **Generate!**
   - Connect to your sampler and generate
   - Each prompt appears exactly where you drew it

### Tips for Best Results

#### For Flux Users:
- ✅ **Enable "Flux Optimize"** (it's on by default) - This uses special mask strength (0.8) that works better than full strength
- ✅ **Use 3-4 regions maximum** - More regions = quality degradation
- ✅ **Increase CFG to 5-7** - Flux needs higher guidance for regional control
- ✅ **Draw larger boxes** - Bigger regions = better control

#### For SDXL Users:
- ✅ **Align to 64px grid** - Matches latent space boundaries
- ✅ **No region limit** - Use as many as you need
- ✅ **Normal CFG values** - 7-9 works great

#### General Tips:
- **Overlapping regions** are processed in order (Region 1 → 2 → 3 → 4)
- **Strength slider** (0.0-10.0) controls region influence:
  - `1.0` = Normal (default)
  - `0.5` = Subtle hint
  - `2.0+` = Strong emphasis
  - `0.0` = Effectively disabled
- **Leave prompts empty** to disable unused regions
- **Fullscreen regions** (x=0, y=0, width=canvas, height=canvas) act as background

---

## 📚 All Available Nodes

### Enhanced (Easy Mode) - RECOMMENDED

#### 🎨 Regional Prompter (SD/SDXL - Easy!)
**Perfect for Stable Diffusion and SDXL**

**Inputs:**
- `clip` - CLIP model from your checkpoint
- `background_prompt` - Overall scene description (multiline text)
- `region1_prompt` through `region4_prompt` - What appears in each box (optional)

**Outputs:**
- `conditioning` - Connect to your sampler
- `width`, `height` - Canvas dimensions (for reference)

**How it works:** Type prompts directly, draw boxes, done! The node handles all CLIP encoding internally.

---

#### 🎨 Regional Prompter (Flux/Chroma - Easy!)
**Perfect for Flux, Chroma, and SD3**

**Inputs:**
- `clip` - CLIP model from your checkpoint
- `width`, `height` - Output image dimensions
- `background_prompt` - Overall scene description (multiline text)
- `region1_prompt` through `region4_prompt` - What appears in each box (optional)
- `flux_optimize` - Enable Flux optimizations (default: ON)

**Outputs:**
- `conditioning` - Connect to your sampler

**Flux Optimizations (when enabled):**
- Softened mask strength (0.8 instead of 1.0) for better blending
- Gentle feathering at region edges
- Automatic warning if too many regions

---

### Advanced Nodes (For Power Users)

#### Multi Area Conditioning (SD/SDXL - Advanced)
Area-based conditioning for traditional Stable Diffusion models. Requires external CLIP Text Encode nodes.

**Inputs:**
- `conditioning0` - Base/background conditioning (connect CLIPTextEncode here)
- `conditioning1`, `conditioning2`, etc. - Regional conditioning (add more via right-click menu)

**Outputs:**
- `conditioning` - Combined regional conditioning
- `resolutionX`, `resolutionY` - Canvas dimensions

**Right-Click Menu:**
- Insert input above/below current
- Swap with input above/below
- Remove currently selected input
- Remove all unconnected inputs

---

#### Multi Area Conditioning (Flux/Chroma - Advanced)
Mask-based conditioning for modern models. Requires external CLIP Text Encode nodes.

**Inputs:**
- `conditioning0` - Base/background conditioning
- `conditioning1`, `conditioning2`, etc. - Regional conditioning
- `width`, `height` - Output dimensions
- `mask_strength` - Mask intensity (0.7-0.85 recommended for Flux, 1.0 for others)

**Output:**
- `conditioning` - Combined mask-based conditioning

**How it works:** Boxes are automatically converted to binary masks. You draw visually, the node handles mask generation.

---

### Utility Nodes

#### Conditioning Upscale
Scale conditioning areas by a multiplier - perfect for hi-res fix workflows.

**Example:** 512x512 regions × scalar=2 → 1024x1024 regions

---

#### Conditioning Stretch
Resize conditioning to fit new dimensions - more flexible than upscale.

**Example:** Transform regions from 512x512 to 1024x768 (proportional scaling)

---

#### Multi Latent Composite (Visual)
Visual interface for compositing multiple latents with positioning and feathering.

**Features:**
- ✅ Automatic bounds checking and clipping
- ✅ Channel compatibility validation
- ✅ Smart feathering with gradient masks
- ✅ Detailed warnings and info messages

---

## 🔧 Advanced Techniques

### Fullscreen/Background Conditioning
Set a region to cover the entire canvas (`x=0, y=0, width=canvas_width, height=canvas_height`) to make it fullscreen. This is perfect for background prompts that should influence the whole image.

### Grid Alignment
The 64px grid overlay helps you align regions to latent space boundaries (VAE works in 8x downscaled space, 64px = 8 latent pixels).

### Strength Control
Every region has a strength slider (0.0-10.0):
- **1.0** - Normal strength (default)
- **0.5** - Subtle influence (region blends more with background)
- **2.0+** - Strong influence (region dominates)
- **0.0** - Effectively disabled

### Overlapping Regions
Regions are processed in order. If boxes overlap:
- Background applies first (fullscreen)
- Region 1 applies on top
- Region 2 applies on top of Region 1
- And so on...

The last region "wins" in overlapping areas (for mask-based conditioning).

### Dynamic Sizing
**Important:** The canvas size can be different from your output size!

For example:
- Draw on a 512x512 canvas
- Generate at 1024x1024 output
- Regions automatically scale 2x

This makes it easy to design compositions at lower resolution, then generate at higher resolution.

---

## ❓ Troubleshooting

### "Workflow metadata missing" error
**Cause:** ComfyUI hasn't saved your workflow yet
**Fix:** Save the workflow (Ctrl+S or Cmd+S), then reload the page

### Canvas doesn't show boxes I drew
**Cause:** Workflow not saved, or coordinates are outside canvas
**Fix:**
1. Save and reload workflow
2. Check that x+width ≤ canvas width and y+height ≤ canvas height
3. Select the region using the `index` dropdown to see where it is

### Flux regions look harsh or over-defined
**Cause:** Flux Optimize is disabled, or using advanced node with mask_strength=1.0
**Fix:**
- Use the Easy node with Flux Optimize ON
- Or set mask_strength to 0.7-0.85 in the advanced node

### Too many regions = bad quality (Flux)
**Cause:** Flux struggles with more than 4 regions
**Fix:** Combine related elements into single regions, or use fewer boxes

### Region has no effect
**Cause:** Prompt is empty, strength is 0.0, or box is too small
**Fix:**
1. Make sure the region prompt has text
2. Check strength slider is at least 0.5
3. Make boxes at least 64x64 pixels

---

## 📝 Changelog

### Version 3.1 (November 22, 2025)
- ✨ **NEW:** Enhanced "Easy" nodes with inline prompts!
  - 🎨 Regional Prompter (SD/SDXL - Easy!)
  - 🎨 Regional Prompter (Flux/Chroma - Easy!)
- ✨ **NEW:** No more external CLIP Text Encode nodes needed
- ✨ **NEW:** Flux-optimized mask strength (0.8) and feathering
- ✨ **NEW:** Up to 4 regions + background in one node
- 📚 **DOCS:** Completely rewritten README for user-friendliness
- 📚 **DOCS:** Added CONTEXT.md for development learnings

### Version 3.0 (November 22, 2025)
- ✨ **NEW:** MultiAreaConditioningMask for Flux/Chroma/SD3 support
- ✨ **NEW:** Comprehensive error handling and validation
- ✨ **NEW:** Bounds checking for MultiLatentComposite
- ✨ **NEW:** Tooltips and descriptions on all inputs
- 🔧 **FIX:** Modernized JavaScript loading (no more file copying!)
- 🔧 **FIX:** Removed debug console.log statements
- 🔧 **FIX:** Fixed graph reference bug in background drawing
- 📚 **DOCS:** Complete compatibility matrix and examples
- 🚀 **PERF:** Improved tensor operations and validation

### Version 2.4 (Original)
- Visual area conditioning interface
- MultiLatentComposite with feathering
- ConditioningUpscale and ConditioningStretch utilities

---

## 🤝 Contributing

Found a bug? Have a feature request?
[Open an issue](https://github.com/EnragedAntelope/ComfyUI_RegionalConditioning/issues) on GitHub!

**Tested with:**
- ComfyUI 0.3.71+
- Stable Diffusion 1.5, SD 2.x, SDXL
- Flux.1-dev, Flux.1-schnell
- Chroma1-Radiance

---

## 📄 License

**GLWT (Good Luck With That) Public License**

See [LICENSE](LICENSE) file for the full text.

TL;DR: Use it however you want, but don't blame us if it breaks! 😄

---

## 🙏 Credits

**Current Maintainer:** EnragedAntelope
**Repository:** [github.com/EnragedAntelope/ComfyUI_RegionalConditioning](https://github.com/EnragedAntelope/ComfyUI_RegionalConditioning)

**Original Author:** Davemane42#0042
**Original Concept:** Visual regional conditioning interface for ComfyUI

**Modernization & Enhancement (2025):**
- Flux/Chroma/SD3 support with mask-based conditioning
- Enhanced "Easy Mode" nodes with inline prompts
- Comprehensive error handling and validation
- User-friendly documentation rewrite

**Special Thanks:**
- ComfyUI community for testing and feedback
- Black Forest Labs for Flux research and documentation
- All contributors who reported issues and suggested improvements

---

## 📸 Example Workflows

### Regional Prompter (Easy Mode)
The simplest workflow possible:

```
Checkpoint Loader → CLIP
                     ↓
Regional Prompter (Flux/Chroma - Easy!)
(Type all prompts directly in this node!)
                     ↓
                 Sampler → VAE Decode → Save Image
```

### Advanced Mode (Original Nodes)
For power users who need shared CLIP encodings:

```
Checkpoint Loader → CLIP → CLIPTextEncode (background)
                            ↓
                     CLIPTextEncode (region 1)
                            ↓
                     CLIPTextEncode (region 2)
                            ↓
            Multi Area Conditioning (collects all)
                            ↓
                        Sampler → VAE Decode → Save Image
```

---

**Enjoy precise regional control in your ComfyUI workflows! 🎨**

**Questions? Check the troubleshooting section above, or open an issue on GitHub.**
