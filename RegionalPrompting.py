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

        # Default template boxes (if workflow not saved yet)
        # Region 1 (red sports car): left side, 200x250px starting at (50, 150)
        # Region 2 (street vendor): right side, 180x250px starting at (280, 150)
        values = [
            [50, 150, 200, 250, 1.0],   # Region 1
            [280, 150, 180, 250, 1.0]    # Region 2
        ]
        resolutionX = 512
        resolutionY = 512

        # Get region data from UI (overrides defaults if workflow saved)
        try:
            if extra_pnginfo and "workflow" in extra_pnginfo and "nodes" in extra_pnginfo["workflow"]:
                for node in extra_pnginfo["workflow"]["nodes"]:
                    if node["id"] == int(unique_id):
                        saved_values = node["properties"].get("values", [])
                        if saved_values:  # Only override if we actually have saved values
                            values = saved_values
                        resolutionX = node["properties"].get("width", 512)
                        resolutionY = node["properties"].get("height", 512)
                        break
        except Exception as e:
            print(f"ℹ️  Using default template boxes and canvas size 512x512")

        # Collect all non-empty prompts
        prompts = [background_prompt, region1_prompt, region2_prompt, region3_prompt, region4_prompt]

        # Encode each prompt using CLIP (standard SD/SDXL encoding)
        encoded_conditionings = []
        for prompt in prompts:
            if prompt and prompt.strip():  # Only encode non-empty prompts
                # Standard CLIP encoding for SD/SDXL
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
                    "tooltip": "Output width - must match your latent/sampler"
                }),
                "height": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": MAX_RESOLUTION,
                    "step": 64,
                    "tooltip": "Output height - must match your latent/sampler"
                }),
                "soften_masks": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Enable feathering at region edges - recommended ON"
                }),
                "background_prompt": ("STRING", {
                    "default": "photo of a city street, high quality",
                    "multiline": True,
                    "tooltip": "Scene description (applies to entire image as base)"
                }),
                "region1_prompt": ("STRING", {
                    "default": "red sports car",
                    "multiline": True,
                    "tooltip": "First region - draw box on canvas to position"
                }),
            },
            "optional": {
                "region2_prompt": ("STRING", {
                    "default": "street vendor",
                    "multiline": True,
                    "tooltip": "Second region (optional - clear to disable)"
                }),
                "region3_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Third region (optional - Flux works best with 3-4 max)"
                }),
                "region4_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Fourth region (optional - Flux works best with 3-4 max)"
                }),
            },
            "hidden": {"extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    FUNCTION = "encode_regions_flux"
    CATEGORY = "Davemane42/Enhanced"
    DESCRIPTION = """Mask-based regional prompting with inline text encoding.

Usage:
1. Connect CLIP from checkpoint
2. Set width/height to match your latent
3. Type prompts for background and regions
4. Draw boxes on canvas to position regions
5. Connect conditioning to sampler

Compatible: Flux, Chroma, SD3, SD3.5, Qwen-Image
Recommended: CFG 1.0-3.5, soften_masks ON, 3-4 regions max for Flux"""

    def encode_regions_flux(self, clip, width, height, soften_masks, background_prompt, region1_prompt,
                           extra_pnginfo, unique_id,
                           region2_prompt="", region3_prompt="", region4_prompt=""):
        """Encode all prompts and apply mask-based regional conditioning for Flux/Chroma/SD3."""

        # Default template boxes (if workflow not saved yet)
        # Region 1 (red sports car): left side, 400x500px starting at (100, 300)
        # Region 2 (street vendor): right side, 350x500px starting at (560, 300)
        values = [
            [100, 300, 400, 500, 1.0],   # Region 1
            [560, 300, 350, 500, 1.0]    # Region 2
        ]

        # Get region data from UI (overrides defaults if workflow saved)
        try:
            if extra_pnginfo and "workflow" in extra_pnginfo and "nodes" in extra_pnginfo["workflow"]:
                for node in extra_pnginfo["workflow"]["nodes"]:
                    if node["id"] == int(unique_id):
                        saved_values = node["properties"].get("values", [])
                        if saved_values:  # Only override if we actually have saved values
                            values = saved_values
                        # Override with property dimensions if available
                        prop_width = node["properties"].get("width", width)
                        prop_height = node["properties"].get("height", height)
                        break
        except Exception as e:
            print(f"ℹ️  Using default template boxes and dimensions {width}x{height}")
            prop_width = width
            prop_height = height

        # Collect all non-empty prompts
        prompts = [background_prompt, region1_prompt, region2_prompt, region3_prompt, region4_prompt]

        # Count non-empty regions (excluding background)
        num_regions = sum(1 for p in prompts[1:] if p and p.strip())

        print(f"\n🎨 Regional Prompter - Processing:")
        print(f"   Dimensions: {width}x{height} (latent: {width//8}x{height//8})")
        print(f"   Regions: {num_regions} active (background + {num_regions} regions)")
        print(f"   Soften masks: {soften_masks}")
        print(f"   Default boxes: {values}")

        if num_regions > 4:
            print(f"⚠️  Warning: {num_regions} regions detected. Flux works best with 3-4 regions maximum.")

        # Encode each prompt using CLIP
        # ComfyUI's CLIP object handles multi-encoder complexity internally
        # Works for all models: Flux (2 encoders), SD3 (3 encoders), Chroma/Qwen (1 encoder), etc.
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

        # Determine mask strength based on soften setting
        # Research shows 0.8 (softer masks) work better than full 1.0 strength for Flux
        # Users can try it for Chroma/SD3 (default ON), disable if they prefer sharper edges
        mask_strength = 0.8 if soften_masks else 1.0

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

            print(f"   Region {i}: '{prompts[i][:40]}...'")
            print(f"      Box: x={x}, y={y}, w={w}, h={h}")
            print(f"      Latent: x={x_latent}, y={y_latent}, w={w_latent}, h={h_latent}")
            print(f"      Mask strength: {mask_strength}, Region strength: {strength}")

            # Apply feathering if softening enabled (gentle edge blending to avoid harsh boundaries)
            if soften_masks:
                # Apply gentle gaussian-like feather at edges (40-60px = 5-8 latent pixels)
                feather_size = min(6, w_latent // 4, h_latent // 4)
                if feather_size > 0:
                    for edge_idx in range(feather_size):
                        fade = (edge_idx + 1) / feather_size * mask_strength
                        # Top edge
                        if y_latent + edge_idx < y_end:
                            mask[0, y_latent + edge_idx, x_latent:x_end] *= (fade / mask_strength)
                        # Bottom edge
                        if y_end - 1 - edge_idx >= y_latent:
                            mask[0, y_end - 1 - edge_idx, x_latent:x_end] *= (fade / mask_strength)
                        # Left edge
                        if x_latent + edge_idx < x_end:
                            mask[0, y_latent:y_end, x_latent + edge_idx] *= (fade / mask_strength)
                        # Right edge
                        if x_end - 1 - edge_idx >= x_latent:
                            mask[0, y_latent:y_end, x_end - 1 - edge_idx] *= (fade / mask_strength)

            # Apply mask to conditioning
            for t in encoded_conditionings[i]:
                n = [t[0], t[1].copy()]
                n[1]['mask'] = mask
                n[1]['strength'] = max(0.0, min(10.0, strength))
                n[1]['set_area_to_bounds'] = False
                combined_conditioning.append(n)

        print(f"   ✅ Generated {len(combined_conditioning)} conditioning blocks")
        print(f"   💡 Tip: Flux works best at CFG 1.0-3.5 with regional prompting\n")

        return (combined_conditioning,)


# Note: These enhanced nodes need the same JavaScript UI as the original nodes
# They will use the canvas interface from MultiAreaConditioning/MultiAreaConditioningMask
