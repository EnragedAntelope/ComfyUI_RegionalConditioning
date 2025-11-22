# Enhanced All-in-One Regional Prompting Nodes
# Created: 2025-11-22
# Inline prompt boxes - no external CLIP Text Encode nodes needed!

import torch
from nodes import MAX_RESOLUTION
import folder_paths

class RegionalPrompterSimple:
    """
    ALL-IN-ONE regional prompting with inline text inputs!

    Just connect your CLIP model, type prompts directly, and draw boxes.
    No need for external CLIP Text Encode nodes!

    Compatible with: SD1.5, SD2.x, SDXL (area-based conditioning)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP", {"tooltip": "CLIP model from your checkpoint"}),
                "background_prompt": ("STRING", {
                    "default": "photo of a city street, high quality",
                    "multiline": True,
                    "tooltip": "Background/scene description (applies to whole image)"
                }),
                "region1_prompt": ("STRING", {
                    "default": "red sports car",
                    "multiline": True,
                    "tooltip": "Prompt for first region/box (clear this to disable)"
                }),
            },
            "optional": {
                "region2_prompt": ("STRING", {
                    "default": "street vendor",
                    "multiline": True,
                    "tooltip": "Prompt for second region (optional - clear this to disable)"
                }),
                "region3_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Prompt for third region (optional - clear this to disable)"
                }),
                "region4_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Prompt for fourth region (optional - clear this to disable)"
                }),
            },
            "hidden": {"extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("CONDITIONING", "INT", "INT")
    RETURN_NAMES = ("conditioning", "width", "height")
    FUNCTION = "encode_regions"
    CATEGORY = "Davemane42/Enhanced"
    DESCRIPTION = """🎨 ALL-IN-ONE Regional Prompting (EASY MODE!)

Just type your prompts and draw boxes - that's it!

✅ No external CLIP Text Encode nodes needed
✅ Simple workflow: CLIP → This Node → Sampler
✅ Up to 4 regions + background
✅ Visual box drawing interface

How to use:
1. Connect CLIP from your checkpoint
2. Type background prompt (whole image)
3. Type region prompts (for each box)
4. Draw boxes on canvas
5. Connect to sampler!

Compatible: SD1.5, SD2.x, SDXL"""

    def encode_regions(self, clip, background_prompt, region1_prompt, extra_pnginfo, unique_id,
                      region2_prompt="", region3_prompt="", region4_prompt=""):
        """Encode all prompts and apply regional conditioning."""

        values = []
        resolutionX = 512
        resolutionY = 512

        # Get canvas dimensions and region data from UI
        try:
            if extra_pnginfo and "workflow" in extra_pnginfo and "nodes" in extra_pnginfo["workflow"]:
                for node in extra_pnginfo["workflow"]["nodes"]:
                    if node["id"] == int(unique_id):
                        values = node["properties"].get("values", [])
                        resolutionX = node["properties"].get("width", 512)
                        resolutionY = node["properties"].get("height", 512)
                        break
        except Exception as e:
            print(f"ℹ️  Using default canvas size 512x512")

        # Collect all non-empty prompts
        prompts = [background_prompt, region1_prompt, region2_prompt, region3_prompt, region4_prompt]

        # Encode each prompt using CLIP
        encoded_conditionings = []
        for prompt in prompts:
            if prompt and prompt.strip():  # Only encode non-empty prompts
                # Use CLIPTextEncode functionality
                tokens = clip.tokenize(prompt)
                cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
                encoded_conditionings.append([[cond, {"pooled_output": pooled}]])
            else:
                encoded_conditionings.append(None)

        # Apply regional conditioning using area-based method
        c = []

        # Background (fullscreen)
        if encoded_conditionings[0]:
            for t in encoded_conditionings[0]:
                c.append(t)

        # Process each region
        for i in range(1, min(len(encoded_conditionings), len(values) + 1)):
            if encoded_conditionings[i] is None:
                continue

            if i - 1 >= len(values):
                continue

            try:
                x, y = int(values[i-1][0]), int(values[i-1][1])
                w, h = int(values[i-1][2]), int(values[i-1][3])
                strength = float(values[i-1][4]) if len(values[i-1]) > 4 else 1.0
            except (IndexError, ValueError, TypeError):
                continue

            # Skip if fullscreen (already added as background)
            if x == 0 and y == 0 and w == resolutionX and h == resolutionY:
                continue

            # Clip to bounds
            if x + w > resolutionX:
                w = max(0, resolutionX - x)
            if y + h > resolutionY:
                h = max(0, resolutionY - y)

            if w == 0 or h == 0:
                continue

            # Apply area to conditioning
            for t in encoded_conditionings[i]:
                n = [t[0], t[1].copy()]
                n[1]['area'] = (h // 8, w // 8, y // 8, x // 8)
                n[1]['strength'] = max(0.0, min(10.0, strength))
                n[1]['min_sigma'] = 0.0
                n[1]['max_sigma'] = 99.0
                c.append(n)

        return (c, int(resolutionX), int(resolutionY))


class RegionalPrompterFlux:
    """
    ALL-IN-ONE regional prompting for FLUX/CHROMA with inline text inputs!

    Just connect your CLIP model, type prompts directly, and draw boxes.
    Automatically converts to masks optimized for Flux!

    Compatible with: Flux, Chroma, SD3, SD3.5 (mask-based conditioning)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP", {"tooltip": "CLIP model from your checkpoint"}),
                "width": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": MAX_RESOLUTION,
                    "step": 64,
                    "tooltip": "Output image width"
                }),
                "height": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": MAX_RESOLUTION,
                    "step": 64,
                    "tooltip": "Output image height"
                }),
                "background_prompt": ("STRING", {
                    "default": "photo of a city street, high quality",
                    "multiline": True,
                    "tooltip": "Background/scene description (applies to whole image)"
                }),
                "region1_prompt": ("STRING", {
                    "default": "red sports car",
                    "multiline": True,
                    "tooltip": "Prompt for first region/box (leave empty to disable)"
                }),
                "use_soft_masks": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Enable soft masks (0.8 strength + feathering). Recommended for Flux (confirmed), may help Chroma/SD3. Disable for full-strength masks (1.0)"
                }),
            },
            "optional": {
                "region2_prompt": ("STRING", {
                    "default": "street vendor",
                    "multiline": True,
                    "tooltip": "Prompt for second region (optional - clear this to disable)"
                }),
                "region3_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Prompt for third region (optional - note: Flux works best with 3-4 regions max)"
                }),
                "region4_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Prompt for fourth region (optional - note: Flux works best with 3-4 regions max)"
                }),
            },
            "hidden": {"extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    FUNCTION = "encode_regions_flux"
    CATEGORY = "Davemane42/Enhanced"
    DESCRIPTION = """🎨 ALL-IN-ONE Flux/Chroma/SD3 Regional Prompting (EASY MODE!)

Just type your prompts and draw boxes - that's it!

✅ No external CLIP Text Encode nodes needed
✅ Simple workflow: CLIP → This Node → Sampler
✅ Soft masks option (0.8 strength + feathering)
✅ Up to 4 regions + background (Flux works best with 3-4 max)
✅ Visual box drawing interface
✅ Comes with example prompts pre-filled!

How to use:
1. Connect CLIP from your checkpoint
2. Review example prompts (or replace with your own)
3. Draw boxes on canvas for each region
4. Enable "Soft Masks" for Flux (recommended)
5. Connect to sampler!

Flux Tips:
• Use 3-4 regions maximum for best results
• Keep "Soft Masks" enabled (0.8 strength works better than 1.0)
• Increase CFG to 5-7 (vs typical 3-5)
• Draw larger regions for better control

Chroma/SD3 Tips:
• Try "Soft Masks" ON first, disable if results look washed out
• No region limit (unlike Flux)

Compatible: Flux, Chroma, SD3, SD3.5"""

    def encode_regions_flux(self, clip, width, height, background_prompt, region1_prompt,
                           use_soft_masks, extra_pnginfo, unique_id,
                           region2_prompt="", region3_prompt="", region4_prompt=""):
        """Encode all prompts and apply mask-based regional conditioning for Flux."""

        values = []

        # Get region data from UI
        try:
            if extra_pnginfo and "workflow" in extra_pnginfo and "nodes" in extra_pnginfo["workflow"]:
                for node in extra_pnginfo["workflow"]["nodes"]:
                    if node["id"] == int(unique_id):
                        values = node["properties"].get("values", [])
                        # Override with property dimensions if available
                        prop_width = node["properties"].get("width", width)
                        prop_height = node["properties"].get("height", height)
                        break
        except Exception as e:
            print(f"ℹ️  Using input dimensions {width}x{height}")
            prop_width = width
            prop_height = height

        # Collect all non-empty prompts
        prompts = [background_prompt, region1_prompt, region2_prompt, region3_prompt, region4_prompt]

        # Count non-empty regions (excluding background)
        num_regions = sum(1 for p in prompts[1:] if p and p.strip())

        if num_regions > 4:
            print(f"⚠️  Warning: {num_regions} regions detected. Flux works best with 3-4 regions maximum.")

        # Encode each prompt using CLIP
        encoded_conditionings = []
        for prompt in prompts:
            if prompt and prompt.strip():
                tokens = clip.tokenize(prompt)
                cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
                encoded_conditionings.append([[cond, {"pooled_output": pooled}]])
            else:
                encoded_conditionings.append(None)

        # Apply mask-based conditioning
        combined_conditioning = []

        # Determine mask strength based on soft mask setting
        # Research shows 0.8 (softer masks) work better for Flux than full 1.0 strength
        # May also benefit Chroma and SD3, but not confirmed
        mask_strength = 0.8 if use_soft_masks else 1.0

        # Background (fullscreen - no mask)
        if encoded_conditionings[0]:
            for t in encoded_conditionings[0]:
                combined_conditioning.append(t)

        # Process each region with masks
        latent_width = width // 8
        latent_height = height // 8

        for i in range(1, min(len(encoded_conditionings), len(values) + 1)):
            if encoded_conditionings[i] is None:
                continue

            if i - 1 >= len(values):
                continue

            try:
                x, y = int(values[i-1][0]), int(values[i-1][1])
                w, h = int(values[i-1][2]), int(values[i-1][3])
                strength = float(values[i-1][4]) if len(values[i-1]) > 4 else 1.0
            except (IndexError, ValueError, TypeError):
                continue

            # Get canvas dimensions
            canvas_width = prop_width if 'prop_width' in locals() else width
            canvas_height = prop_height if 'prop_height' in locals() else height

            # Skip fullscreen (already added as background)
            if x == 0 and y == 0 and w == canvas_width and h == canvas_height:
                continue

            # Scale to output dimensions if needed
            if canvas_width != width or canvas_height != height:
                x = int(x * width / canvas_width)
                y = int(y * height / canvas_height)
                w = int(w * width / canvas_width)
                h = int(h * height / canvas_height)

            # Clip to bounds
            x = max(0, min(x, width))
            y = max(0, min(y, height))
            w = max(0, min(w, width - x))
            h = max(0, min(h, height - y))

            if w == 0 or h == 0:
                continue

            # Convert to latent space
            x_latent = x // 8
            y_latent = y // 8
            w_latent = max(1, w // 8)
            h_latent = max(1, h // 8)

            # Create mask with Flux-optimized strength
            mask = torch.zeros((1, latent_height, latent_width), dtype=torch.float32)

            x_end = min(x_latent + w_latent, latent_width)
            y_end = min(y_latent + h_latent, latent_height)

            # Fill mask with specified strength
            mask[0, y_latent:y_end, x_latent:x_end] = mask_strength

            # Apply feathering if soft masks enabled (gentle edge blending)
            if use_soft_masks:
                # Apply gentle gaussian-like feather at edges (40-60px = 5-8 latent pixels)
                feather_size = min(6, w_latent // 4, h_latent // 4)
                if feather_size > 0:
                    for i in range(feather_size):
                        fade = (i + 1) / feather_size * mask_strength
                        # Top edge
                        if y_latent + i < y_end:
                            mask[0, y_latent + i, x_latent:x_end] *= (fade / mask_strength)
                        # Bottom edge
                        if y_end - 1 - i >= y_latent:
                            mask[0, y_end - 1 - i, x_latent:x_end] *= (fade / mask_strength)
                        # Left edge
                        if x_latent + i < x_end:
                            mask[0, y_latent:y_end, x_latent + i] *= (fade / mask_strength)
                        # Right edge
                        if x_end - 1 - i >= x_latent:
                            mask[0, y_latent:y_end, x_end - 1 - i] *= (fade / mask_strength)

            # Apply mask to conditioning
            for t in encoded_conditionings[i]:
                n = [t[0], t[1].copy()]
                n[1]['mask'] = mask
                n[1]['strength'] = max(0.0, min(10.0, strength))
                n[1]['set_area_to_bounds'] = False
                combined_conditioning.append(n)

        return (combined_conditioning,)


# Note: These enhanced nodes need the same JavaScript UI as the original nodes
# They will use the canvas interface from MultiAreaConditioning/MultiAreaConditioningMask
