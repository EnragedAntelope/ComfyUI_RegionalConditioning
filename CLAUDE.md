# CLAUDE.md - AI Assistant Development Guide

**Last Updated:** November 22, 2025
**ComfyUI Version:** 0.3.71
**Repository:** EnragedAntelope/ComfyUI_RegionalConditioning

---

## ⚠️ CRITICAL: Read This First

**IMPORTANT:** Past development decisions in this repository have NOT always resulted in working code. Always verify assumptions through testing before considering something "done."

### Golden Rules for AI Assistants

1. **ALWAYS UPDATE CONTEXT.md** - Document what works AND what doesn't work
2. **VERIFY BEFORE CLAIMING** - Test actual behavior, don't assume based on documentation
3. **USE CURRENT RESOURCES** - Only trust resources from May 2025 or later for ComfyUI/model compatibility
4. **DOCUMENT FAILURES** - Failed approaches are as valuable as successful ones
5. **TEST WITH REAL MODELS** - Theoretical compatibility ≠ actual working code

---

## Project Overview

### What This Is

ComfyUI Regional Conditioning is a custom node extension that allows users to apply different prompts to different regions of an image. Think of it as "Photoshop layers for AI prompts" - you can have a red car in one area, a street vendor in another, all in a single generation.

### Core Architecture

```
ComfyUI_RegionalConditioning/
├── RegionalPrompting.py          # Main node implementations (Python)
├── __init__.py                   # Node registration and exports
├── js/
│   ├── RegionalPrompting.js      # Canvas UI for drawing boxes
│   └── utils.js                  # Shared utilities (colors, sizing)
├── CONTEXT.md                    # ⭐ MUST READ - Technical learnings
├── REVIEW.md                     # Comprehensive code review
└── README.md                     # User-facing documentation
```

### Two Node Types (Two Different Technologies)

| Node | Display Name | Technology | Models |
|------|-------------|------------|---------|
| `RegionalPrompterSimple` | Regional Prompter (Area-Based) | `ConditioningSetArea` | SD1.5, SD2.x, SDXL |
| `RegionalPrompterFlux` | Regional Prompter (Mask-Based) | Binary masks + feathering | Flux, Chroma, SD3, SD3.5, others |

**Why two nodes?** Different model architectures require different conditioning methods. Area-based is more efficient for older SD models. Mask-based is required for newer models like Flux.

---

## Codebase Structure

### Python Code (`RegionalPrompting.py`)

**Two main classes:**

```python
class RegionalPrompterSimple:
    """Area-based conditioning for SD/SDXL"""
    def encode_regions(self, clip, background_prompt, region1_prompt, ...):
        # 1. Parse region boxes from UI canvas
        # 2. Encode prompts using CLIP
        # 3. Apply area-based conditioning (height, width, y, x order!)
        # 4. Return combined conditioning
```

```python
class RegionalPrompterFlux:
    """Mask-based conditioning for Flux/Chroma/SD3"""
    def encode_regions_flux(self, clip, width, height, soften_masks, ...):
        # 1. Parse region boxes and scale to output dimensions
        # 2. Encode prompts using CLIP (universal method)
        # 3. Create binary masks with optional feathering
        # 4. Apply masks to conditioning
        # 5. Return combined conditioning
```

### JavaScript Code (`js/`)

**`RegionalPrompting.js`** - Main UI logic
- Canvas widget for drawing region boxes
- Mouse interaction (drag to move, resize)
- Grid overlay (64px for latent alignment)
- Color-coded regions
- Dynamic syncing with width/height inputs

**`utils.js`** - Shared utilities
- `getDrawColor(percent, alpha)` - HSL color generation
- `computeCanvasSize(node, size)` - Dynamic canvas sizing
- Widget transformation functions

### Critical Files You Must Read

1. **CONTEXT.md** (⭐ HIGHEST PRIORITY)
   - Technical learnings from actual testing
   - What works vs what doesn't work
   - Known bugs and workarounds
   - Model compatibility matrix
   - **UPDATE THIS AFTER EVERY SIGNIFICANT CHANGE**

2. **REVIEW.md**
   - Comprehensive code review
   - Quality assessment
   - Future improvements roadmap

3. **README.md**
   - User-facing documentation
   - Keep this simple and beginner-friendly

---

## Development Workflows

### Making Changes to Nodes

```bash
# 1. Read CONTEXT.md to understand current state
cat CONTEXT.md

# 2. Make changes to RegionalPrompting.py
# 3. Test in ComfyUI (don't assume it works!)
# 4. Document findings in CONTEXT.md
# 5. Update README.md if user-facing behavior changed
# 6. Commit with descriptive message
```

### Testing Protocol

**NEVER skip testing. Here's the minimum:**

1. **Basic Functionality Test**
   ```
   - Add node to workflow
   - Verify canvas appears
   - Draw a box
   - Enter prompts
   - Run generation
   - Check output matches expectations
   ```

2. **Edge Cases**
   ```
   - Empty prompts
   - Overlapping boxes
   - Boxes outside canvas bounds
   - Very small boxes (< 64px)
   - Maximum regions (4+)
   ```

3. **Model Compatibility** (if claiming support)
   ```
   - Load actual checkpoint
   - Test with real generation
   - Verify regions appear correctly
   - Document CFG/strength settings that work
   ```

### Git Workflow

```bash
# Current branch (check git status)
git status

# Make changes, test thoroughly

# Stage and commit
git add .
git commit -m "Clear description of what changed and why"

# Push to designated branch
git push -u origin claude/claude-md-miac338uzhm3oi0z-01TWohzd1WDYgZYMuP6BKp8a
```

**Commit Message Guidelines:**
- Start with verb: "Fix", "Add", "Update", "Remove"
- Be specific: ❌ "Fix bug" ✅ "Fix IndexError in feathering loop by renaming variable"
- Reference impact: "Fixes canvas not loading in web-based ComfyUI"

---

## Key Conventions & Patterns

### CLIP Encoding (Universal Pattern)

**CRITICAL:** This pattern works for ALL models (SD, SDXL, Flux, SD3, etc.)

```python
# DO THIS (works everywhere):
tokens = clip.tokenize(prompt)
cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
encoded = [[cond, {"pooled_output": pooled}]]

# DON'T try to detect encoder count or use special methods
# ComfyUI's CLIP object handles multi-encoder complexity internally
```

**Why this works:** ComfyUI abstracts the complexity of 1, 2, 3, or 4 text encoders internally.

### Latent Space Conversion

**ALL coordinates must be divided by 8** (VAE downscaling factor):

```python
# Pixel space → Latent space
x_latent = x // 8
y_latent = y // 8
w_latent = w // 8
h_latent = h // 8

# For area-based conditioning (note the order!):
area = (h // 8, w // 8, y // 8, x // 8)  # height, width, y, x
```

### Mask Creation Pattern (Flux/Chroma/SD3)

```python
# Create mask tensor (latent dimensions)
mask = torch.zeros((1, latent_height, latent_width), dtype=torch.float32)

# Fill region with strength
mask_strength = 0.8 if soften_masks else 1.0
mask[0, y_latent:y_end, x_latent:x_end] = mask_strength

# Optional feathering (if soften_masks enabled)
feather_size = min(6, w_latent // 4, h_latent // 4)
for i in range(feather_size):
    fade = (i + 1) / feather_size * mask_strength
    # Apply fade to all four edges...

# Apply to conditioning
conditioning[1]['mask'] = mask
conditioning[1]['strength'] = strength
conditioning[1]['set_area_to_bounds'] = False
```

### Error Handling Pattern

**Always fail gracefully, never crash:**

```python
try:
    # Attempt to parse metadata
    if extra_pnginfo and "workflow" in extra_pnginfo:
        values = node["properties"].get("values", [])
except Exception as e:
    print(f"ℹ️  Using defaults: {str(e)}")
    values = default_values  # Always have a fallback!
```

**Console message conventions:**
- `ℹ️` - Informational (using defaults, helpful tips)
- `⚠️` - Warning (non-fatal issues, suggestions)
- `❌` - Error (something failed, user action needed)
- `✅` - Success confirmation
- `💡` - Tips and recommendations

### Input Validation Pattern

```python
# Bounds checking
x = max(0, min(x, width))
y = max(0, min(y, height))
w = max(0, min(w, width - x))
h = max(0, min(h, height - y))

# Skip invalid regions (don't crash)
if w == 0 or h == 0:
    continue

# Strength clamping
strength = max(0.0, min(10.0, strength))
```

---

## Critical Technical Details

### JavaScript Widget Callbacks (FRAGILE!)

**Context binding is tricky.** This pattern works:

```javascript
const widthWidget = this.widgets.find(w => w.name === "width");
if (widthWidget) {
    const originalCallback = widthWidget.callback;

    // Capture node reference in closure, call original with widget context
    widthWidget.callback = function(value) {
        node.properties["width"] = value;
        if (originalCallback) {
            originalCallback.call(this, value);  // 'this' = widget!
        }
    };
}
```

**DON'T use `.bind(this)` on callbacks** - breaks original callback context.

### WEB_DIRECTORY Export (REQUIRED!)

**Without this, JavaScript files won't load at all:**

```python
# In __init__.py
import os
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "js")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
```

### Canvas Widget Critical Pattern

```javascript
// Must set width/height attributes (not just CSS)
canvas.width = widgetWidth;   // Internal drawing resolution
canvas.height = widgetHeight;

// CSS controls display size
canvas.style.width = `${displayWidth}px`;
canvas.style.height = `${displayHeight}px`;

// Force initial size computation
setTimeout(() => computeCanvasSize(node, node.size), 100);
```

### Default Template Boxes

**Both nodes have default example boxes** (before workflow saved):

```python
# RegionalPrompterSimple (512x512 canvas)
values = [
    [50, 150, 200, 250, 1.0],   # Region 1: red sports car (left)
    [280, 150, 180, 250, 1.0]   # Region 2: street vendor (right)
]

# RegionalPrompterFlux (1024x1024 canvas)
values = [
    [100, 300, 400, 500, 1.0],  # Region 1: red sports car (left)
    [560, 300, 350, 500, 1.0]   # Region 2: street vendor (right)
]
```

**Why?** First-time users see working example immediately.

---

## Model Compatibility (Verify Before Claiming!)

### Confirmed Working ✅

| Model | Node | Settings | Verified |
|-------|------|----------|----------|
| SD 1.5 | RegionalPrompterSimple | Default | ✅ Yes |
| SDXL | RegionalPrompterSimple | Default | ✅ Yes |
| Flux | RegionalPrompterFlux | soften_masks=True, CFG 1.0-3.5 | ✅ Yes |

### Theoretically Compatible (NEEDS TESTING!) ⏳

| Model | Node | Notes |
|-------|------|-------|
| Chroma | RegionalPrompterFlux | Flux-based architecture, likely works |
| SD3/SD3.5 | RegionalPrompterFlux | Supports mask conditioning |
| Qwen-Image | RegionalPrompterFlux | Unknown, needs checkpoint testing |

### Not Supported ❌

| Model | Reason |
|-------|--------|
| WAN 2.2 | Video-focused architecture, needs research |

**IMPORTANT:** Don't claim support without actual testing with real checkpoints!

---

## Common Tasks & How to Approach Them

### Task: Add Support for New Model

```markdown
1. Research the model's conditioning method
   - Does it use area-based or mask-based conditioning?
   - How many text encoders does it have?
   - What are optimal CFG/strength settings?

2. Use current resources (2025+ only!)
   - Check ComfyUI GitHub issues
   - Search for recent discussions
   - Look for example workflows

3. Test with actual checkpoint
   - Don't assume it works
   - Try both nodes
   - Document what works and what fails

4. Update CONTEXT.md
   - Add to compatibility matrix
   - Document optimal settings
   - Note any quirks or limitations

5. Update README.md if confirmed working
   - Add to compatibility list
   - Include recommended settings
```

### Task: Fix a Bug

```markdown
1. Reproduce the bug reliably
   - Exact steps to trigger
   - Error messages
   - Environment details

2. Identify root cause
   - Read relevant code carefully
   - Check CONTEXT.md for known issues
   - Add debug print statements

3. Fix and verify
   - Make minimal change
   - Test thoroughly
   - Check for regressions

4. Document in CONTEXT.md
   - What the bug was
   - What caused it
   - How it was fixed
   - Add to "Critical Bugfixes" section

5. Commit with detailed message
   - Include symptom and fix
   - Reference file:line if applicable
```

### Task: Improve UX

```markdown
1. Identify pain point
   - Read user feedback
   - Test first-time experience
   - Find confusing elements

2. Propose solution
   - Keep it simple
   - Don't over-engineer
   - Consider backward compatibility

3. Implement and test
   - Update Python and/or JavaScript
   - Test in actual workflow
   - Get feedback if possible

4. Update documentation
   - CONTEXT.md (implementation notes)
   - README.md (if user-facing)
   - Node descriptions/tooltips

5. Document in CONTEXT.md
   - Add to "UX Improvements" section
   - Note the before/after
   - Track impact
```

### Task: Optimize Performance

```markdown
1. Measure first
   - What operation is slow?
   - How slow (ms, seconds)?
   - Is it actually a problem?

2. Profile before optimizing
   - Don't optimize based on assumptions
   - Measure actual bottlenecks

3. Optimize conservatively
   - One change at a time
   - Verify correctness after each change
   - Measure improvement

4. Document in CONTEXT.md
   - What was slow
   - What you changed
   - Performance improvement (with numbers)
```

---

## Testing Guidelines

### Minimum Testing Requirements

Before claiming something works:

1. **Unit-level Test**
   - Does the function return expected output?
   - Are edge cases handled?
   - No errors in console?

2. **Integration Test**
   - Does the node appear in ComfyUI?
   - Can you connect it in a workflow?
   - Does it execute without errors?

3. **Output Test**
   - Does the generated image match expectations?
   - Do regions appear where they should?
   - Quality acceptable?

4. **Edge Case Test**
   - Empty prompts
   - Missing metadata
   - Extreme values
   - Invalid inputs

### What to Document

**In CONTEXT.md after testing:**

```markdown
## Testing Results - [Model Name] - [Date]

### Setup
- Model: [exact model name/version]
- ComfyUI: [version]
- Node: [RegionalPrompterSimple or RegionalPrompterFlux]
- Settings: [width, height, soften_masks, CFG, strength]

### Results
✅ Works / ⏳ Partial / ❌ Failed

### Findings
- [What worked well]
- [What didn't work]
- [Optimal settings discovered]
- [Unexpected behavior]

### Recommendations
- [Suggested settings for users]
- [Known limitations]
- [Future improvements]
```

---

## Anti-Patterns (Don't Do This!)

### ❌ Assuming Compatibility

```python
# DON'T:
# "Flux uses 2 encoders, so SD3 probably works the same way"

# DO:
# "SD3 uses 3 encoders. Testing needed to verify compatibility."
# [Test with actual SD3 checkpoint]
# [Document actual results in CONTEXT.md]
```

### ❌ Using Outdated Information

```python
# DON'T:
# "This tutorial from 2023 says to use hasattr() to detect Flux"

# DO:
# "ComfyUI 0.3.71 (2025) uses universal encode_from_tokens"
# [Verify with current ComfyUI source code]
# [Test with current models]
```

### ❌ Claiming Success Without Testing

```python
# DON'T:
def encode_regions_chroma(...):
    # "This should work for Chroma"
    return result

# DO:
def encode_regions_chroma(...):
    # Tested with Chroma1-Radiance on 2025-11-22
    # Settings: soften_masks=True, CFG=2.0, strength=1.0
    # Result: ✅ Regions appear correctly
    # [Document in CONTEXT.md]
    return result
```

### ❌ Over-Engineering

```python
# DON'T:
class AbstractRegionalConditioningStrategy:
    def create_factory(self):
        return RegionalConditioningFactoryBuilder()...

# DO:
def encode_regions(clip, prompts, boxes):
    # Simple, direct, works
    return conditioning
```

### ❌ Silent Failures

```python
# DON'T:
try:
    result = parse_boxes(data)
except:
    pass  # Silent failure - user has no idea what went wrong

# DO:
try:
    result = parse_boxes(data)
except Exception as e:
    print(f"⚠️  Warning: Could not parse boxes: {str(e)}")
    result = default_boxes  # Fallback with explanation
```

---

## Updating CONTEXT.md (Your Most Important Job!)

### When to Update

- ✅ After testing a new model
- ✅ After fixing a bug
- ✅ After discovering a quirk or limitation
- ✅ After implementing a feature
- ✅ After finding optimal settings
- ✅ When something DOESN'T work (critical!)

### What to Document

**Successful Findings:**
```markdown
### [Model Name] Compatibility (Tested 2025-11-22)
- **Status:** ✅ Working
- **Node:** RegionalPrompterFlux
- **Optimal Settings:**
  - soften_masks: True
  - CFG: 2.0-3.0
  - Strength: 1.0-1.5
- **Notes:** Works best with 3-4 regions maximum
- **Test Checkpoint:** [exact model file name]
```

**Failed Attempts:**
```markdown
### [Approach Name] - DOES NOT WORK ❌
- **Date:** 2025-11-22
- **Attempted:** [what you tried]
- **Expected:** [what you thought would happen]
- **Actual:** [what actually happened]
- **Error:** [error messages]
- **Conclusion:** [why it doesn't work]
- **Alternative:** [what to do instead]
```

**Learnings:**
```markdown
### Critical Discovery: [Title]
- **Finding:** [what you learned]
- **Impact:** [why it matters]
- **Before:** [old understanding]
- **After:** [new understanding]
- **Evidence:** [how you verified this]
```

---

## Resources & References

### Current Resources (2025+)

- **ComfyUI Official:** https://github.com/comfyanonymous/ComfyUI
- **ComfyUI Docs:** https://docs.comfy.org/
- **ComfyUI Nodes:** https://docs.comfy.org/essentials/custom_node_overview

### Checking Information Currency

```bash
# When researching, ask:
1. Is this resource from 2025 or later?
2. Is this for ComfyUI 0.3.x or later?
3. Has the API changed since this was written?
4. Can I verify this with current source code?
```

### Verifying Claims

```python
# Don't trust documentation blindly
# Read the actual source code:

# Example: Verify CLIP encoding method
# 1. Find ComfyUI installation
# 2. Read comfy/sd1_clip.py, comfy/sd2_clip.py, etc.
# 3. Confirm the method exists and works as described
# 4. Test with actual model
```

---

## Quick Reference

### File Locations

```
RegionalPrompting.py:18-164    → RegionalPrompterSimple class
RegionalPrompting.py:167-411   → RegionalPrompterFlux class
__init__.py:9-17               → Node registration
js/RegionalPrompting.js:9-400  → Canvas widget implementation
js/utils.js:120-178            → Canvas sizing logic
```

### Key Variables

```python
values        # [[x, y, w, h, strength], ...] - region boxes
resolutionX   # Canvas width (may differ from output width)
resolutionY   # Canvas height (may differ from output height)
width/height  # Output dimensions (must match latent)
soften_masks  # Enable 0.8 strength + feathering
mask_strength # 0.8 if soften_masks else 1.0
```

### Console Message Format

```python
print(f"ℹ️  Info message")        # Blue, informational
print(f"⚠️  Warning message")     # Yellow, non-critical
print(f"❌ Error message")        # Red, problem occurred
print(f"✅ Success message")      # Green, confirmation
print(f"💡 Tip message")          # Light, suggestion
```

---

## Final Reminders for AI Assistants

1. **ALWAYS UPDATE CONTEXT.md** - It's the source of truth
2. **TEST BEFORE CLAIMING** - Assumptions are often wrong
3. **DOCUMENT FAILURES** - They prevent repeating mistakes
4. **USE CURRENT INFO** - Pre-2025 resources may be outdated
5. **FAIL GRACEFULLY** - Never crash, always have fallbacks
6. **KEEP IT SIMPLE** - Minimal changes, focused solutions
7. **VERIFY EVERYTHING** - Read source code, test with real models

**When in doubt:** Test it, document it, ask the user.

---

**Maintained by:** EnragedAntelope
**Repository:** https://github.com/EnragedAntelope/ComfyUI_RegionalConditioning
**License:** MIT
