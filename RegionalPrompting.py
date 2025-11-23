# Enhanced All-in-One Regional Prompting Nodes
# Created: 2025-11-22
# Inline prompt boxes - no external CLIP Text Encode nodes needed!

import torch
from nodes import MAX_RESOLUTION
import folder_paths

class EasyRegionSimple:
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
                    "tooltip": "Region 1 - First region/box (see canvas below)"
                }),
            },
            "optional": {
                "region2_prompt": ("STRING", {
                    "default": "giraffe wearing sunglasses",
                    "multiline": True,
                    "tooltip": "Region 2 - Second region/box (see canvas below)"
                }),
                "region3_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Region 3 - Third region/box (see canvas below)"
                }),
                "region4_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Region 4 - Fourth region/box (see canvas below)"
                }),
            },
            "hidden": {
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
                "region_boxes": "STRING"
            },
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    FUNCTION = "encode_regions"
    CATEGORY = "EasyRegion"
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

    def encode_regions(self, clip, background_prompt, region1_prompt, extra_pnginfo, unique_id, region_boxes="",
                      region2_prompt="", region3_prompt="", region4_prompt=""):
        """Encode all prompts and apply regional conditioning."""

        # Default template boxes (fallback if no data from UI)
        values = [
            [41, 102, 138, 307, 1.0],   # Region 1 - percentage-based for 512x512
            [360, 77, 140, 348, 1.0]    # Region 2 - percentage-based for 512x512
        ]
        resolutionX = 512
        resolutionY = 512

        # First try to parse from hidden widget (works on fresh nodes)
        if region_boxes:
            try:
                import json
                parsed = json.loads(region_boxes)
                if parsed and len(parsed) > 0:
                    values = parsed
                    print(f"ℹ️  Using region boxes from widget: {values}")
            except Exception as e:
                print(f"⚠️  Failed to parse region_boxes widget: {e}")

        # Fallback: Get region data from saved workflow (overrides if available)
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
                strength = float(values[i-1][4]) if len(values[i-1]) > 4 else 2.0
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

        return (c,)


class EasyRegionMask:
    """
    ALL-IN-ONE regional prompting with inline text inputs!

    Just connect your CLIP model, type prompts directly, and draw boxes.
    Uses mask-based conditioning for maximum model compatibility.

    Compatible with modern mask-based models (see README for model-specific tips)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP", {"tooltip": "CLIP model from your checkpoint"}),
                "width": ("INT", {
                    "default": 1344,
                    "min": 64,
                    "max": MAX_RESOLUTION,
                    "step": 64,
                    "tooltip": "Output width - must match your latent/sampler"
                }),
                "height": ("INT", {
                    "default": 768,
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
                    "default": "photo of empty city street at night, high quality",
                    "multiline": True,
                    "tooltip": "Scene description (applies to entire image as base)"
                }),
            },
            "optional": {
                "background_strength": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                    "tooltip": "Background conditioning strength (lower = regions show more, user-tested: 0.7-1.2)"
                }),
                "region1_prompt": ("STRING", {
                    "default": "red sports car",
                    "multiline": True,
                    "tooltip": "Region 1 - TIP: Include size/detail keywords (e.g. 'closeup', 'full body', 'large')"
                }),
                "region1_strength": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                    "tooltip": "Region 1 strength (user-tested: 0.7, range: 0.5-1.0)"
                }),
                "region2_prompt": ("STRING", {
                    "default": "closeup full body giraffe wearing sunglasses",
                    "multiline": True,
                    "tooltip": "Region 2 - TIP: Include size/detail keywords (e.g. 'closeup', 'full body', 'large')"
                }),
                "region2_strength": ("FLOAT", {
                    "default": 0.8,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                    "tooltip": "Region 2 strength (user-tested: 0.8, range: 0.6-1.2)"
                }),
                "region3_prompt": ("STRING", {
                    "default": "blue bird flying",
                    "multiline": True,
                    "tooltip": "Region 3 - Optional third region"
                }),
                "region3_strength": ("FLOAT", {
                    "default": 1.5,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                    "tooltip": "Region 3 strength (user-tested: 1.5, range: 1.0-2.0)"
                }),
                "region4_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Region 4 - Optional fourth region"
                }),
                "region4_strength": ("FLOAT", {
                    "default": 2.5,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                    "tooltip": "Region 4 strength (recommended: 2.5-3.0, higher values may cause artifacts)"
                }),
            },
            "hidden": {
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
                "region_boxes": "STRING"
            },
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    FUNCTION = "encode_regions_mask"
    CATEGORY = "EasyRegion"
    DESCRIPTION = """Mask-based regional prompting for modern diffusion models.

Quick Start:
1. Connect CLIP from checkpoint
2. Set width/height to match your latent exactly
3. Type prompts (background + regions)
4. Adjust per-region strength (defaults: 0.7, 0.8, 1.5, 2.5)
5. Draw/adjust boxes on canvas

See README for model-specific tips and recommended settings."""

    def encode_regions_mask(self, clip, width, height, background_strength, soften_masks, background_prompt, region1_prompt,
                           extra_pnginfo, unique_id, region_boxes="",
                           region1_strength=0.7, region2_prompt="", region2_strength=0.8,
                           region3_prompt="", region3_strength=1.5, region4_prompt="", region4_strength=2.5):
        """Encode all prompts and apply mask-based regional conditioning."""

        # Default template boxes (fallback if no data from UI)
        # Matches user's 1344x768 workflow with 3 regions
        values = [
            [0, 320, 368, 462, 2.0],      # Region 1 - red sports car (left)
            [448, 64, 384, 704, 2.0],     # Region 2 - giraffe (center-right)
            [945, 0, 378, 256, 2.0]       # Region 3 - blue bird (top-right)
        ]

        # First try to parse from hidden widget (works on fresh nodes)
        if region_boxes:
            try:
                import json
                parsed = json.loads(region_boxes)
                if parsed and len(parsed) > 0:
                    values = parsed
                    print(f"ℹ️  Using region boxes from widget: {values}")
            except Exception as e:
                print(f"⚠️  Failed to parse region_boxes widget: {e}")

        # Fallback: Get region data from saved workflow (overrides if available)
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
        print(f"   Background strength: {background_strength}")
        print(f"   Region strengths: [{region1_strength}, {region2_strength}, {region3_strength}, {region4_strength}]")
        print(f"   Regions: {num_regions} active (background + {num_regions} regions)")
        print(f"   Soften masks: {soften_masks}")
        print(f"   Default boxes: {values}")

        if num_regions > 4:
            print(f"⚠️  Warning: {num_regions} regions detected. Most models work best with 3-4 regions maximum.")

        # Concatenate background to regional prompts for visual coherence
        # This ensures all regions share the same scene context
        prompts_final = []
        for i, prompt in enumerate(prompts):
            if i == 0:  # Background
                prompts_final.append(prompt if prompt and prompt.strip() else "")
            else:  # Regional prompts - prepend background for unified composition
                if prompt and prompt.strip():
                    combined = f"{background_prompt}, {prompt}" if background_prompt and background_prompt.strip() else prompt
                    prompts_final.append(combined)
                    print(f"   📝 Region {i} combined prompt: '{combined[:60]}...'")
                else:
                    prompts_final.append("")

        # Encode each prompt using CLIP
        # ComfyUI's CLIP object handles multi-encoder complexity internally
        encoded_conditionings = []

        for prompt in prompts_final:
            if prompt and prompt.strip():
                tokens = clip.tokenize(prompt)
                cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
                encoded_conditionings.append([[cond, {"pooled_output": pooled}]])
            else:
                encoded_conditionings.append(None)

        # Apply mask-based conditioning
        combined_conditioning = []

        # Mask tensor values: use 1.0 (full binary mask), let mask_strength param control intensity
        # The per-region strength parameter in conditioning dict controls actual strength
        mask_tensor_value = 1.0  # Always use binary mask (0.0 or 1.0)

        # Background (fullscreen - no mask)
        # Apply background_strength to allow users to reduce background influence
        if encoded_conditionings[0]:
            for t in encoded_conditionings[0]:
                n = [t[0], t[1].copy()]
                if background_strength != 1.0:
                    # Scale the conditioning tensor by background_strength
                    n[0] = t[0] * background_strength
                combined_conditioning.append(n)

        # Per-region strength values from inputs (not canvas)
        region_strengths = [region1_strength, region2_strength, region3_strength, region4_strength]

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
                # Use per-region strength from inputs instead of canvas values
                strength = region_strengths[i-1] if i-1 < len(region_strengths) else 5.0
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

            # Create binary mask for region
            mask = torch.zeros((1, latent_height, latent_width), dtype=torch.float32)

            x_end = min(x_latent + w_latent, latent_width)
            y_end = min(y_latent + h_latent, latent_height)

            # Fill mask region with 1.0 (binary mask)
            mask[0, y_latent:y_end, x_latent:x_end] = mask_tensor_value

            print(f"   Region {i}: '{prompts[i][:40]}...'")
            print(f"      Box: x={x}, y={y}, w={w}, h={h}")
            print(f"      Latent: x={x_latent}, y={y_latent}, w={w_latent}, h={h_latent}")
            print(f"      Mask: binary 1.0, Conditioning strength: {strength}")

            # Create separate feathered mask for visual blending
            # Keep original mask binary for attention control
            feathered_mask = mask.clone()

            # Apply feathering if enabled (gentle edge blending)
            if soften_masks:
                # Apply gaussian-like feather at edges (40-60px = 5-8 latent pixels)
                feather_size = min(6, w_latent // 4, h_latent // 4)
                if feather_size > 0:
                    for edge_idx in range(feather_size):
                        fade = (edge_idx + 1) / feather_size  # 0.0 to 1.0 gradient
                        # Top edge
                        if y_latent + edge_idx < y_end:
                            feathered_mask[0, y_latent + edge_idx, x_latent:x_end] = fade
                        # Bottom edge
                        if y_end - 1 - edge_idx >= y_latent:
                            feathered_mask[0, y_end - 1 - edge_idx, x_latent:x_end] = fade
                        # Left edge
                        if x_latent + edge_idx < x_end:
                            feathered_mask[0, y_latent:y_end, x_latent + edge_idx] = torch.minimum(feathered_mask[0, y_latent:y_end, x_latent + edge_idx], torch.tensor(fade))
                        # Right edge
                        if x_end - 1 - edge_idx >= x_latent:
                            feathered_mask[0, y_latent:y_end, x_end - 1 - edge_idx] = torch.minimum(feathered_mask[0, y_latent:y_end, x_end - 1 - edge_idx], torch.tensor(fade))

            # Apply mask-based conditioning with attention masking
            # Background concatenation provides scene context
            # Attention masking forces correct spatial placement
            for t in encoded_conditionings[i]:
                n = [t[0], t[1].copy()]
                n[1]['mask'] = feathered_mask  # Feathered for smooth visual blending
                n[1]['mask_strength'] = max(0.0, min(10.0, strength))
                n[1]['set_area_to_bounds'] = False

                # Create attention mask for precise regional control
                # This FORCES the model to generate content in the correct region
                cond_tensor = t[0]  # [batch, seq_len, hidden_dim]
                txt_tokens = cond_tensor.shape[1]
                img_tokens = latent_height * latent_width
                total_tokens = txt_tokens + img_tokens

                # Initialize blocking all (-10000), then enable specific paths
                attention_mask = torch.full((1, total_tokens, total_tokens), -10000.0, dtype=torch.float32)

                # Enable text-to-text attention (prompts can interact)
                attention_mask[0, :txt_tokens, :txt_tokens] = 0.0

                # VECTORIZED: Enable text→image and image→text ONLY for this region's pixels
                # This prevents "bird" text from affecting car region pixels
                # Performance: ~1000x faster than nested loops for large regions
                y_coords = torch.arange(y_latent, y_end, dtype=torch.long)
                x_coords = torch.arange(x_latent, x_end, dtype=torch.long)
                y_grid, x_grid = torch.meshgrid(y_coords, x_coords, indexing='ij')
                img_token_indices = txt_tokens + (y_grid.flatten() * latent_width + x_grid.flatten())

                # Enable txt→img (text can influence these image pixels)
                attention_mask[0, :txt_tokens, img_token_indices] = 0.0
                # Enable img→txt (these image pixels can attend to text)
                attention_mask[0, img_token_indices, :txt_tokens] = 0.0

                # VECTORIZED: Enable image→image ONLY within this region
                # Uses broadcasting to create [N, N] assignment efficiently
                img_idx_row = img_token_indices.unsqueeze(1)  # [N, 1]
                img_idx_col = img_token_indices.unsqueeze(0)  # [1, N]
                attention_mask[0, img_idx_row, img_idx_col] = 0.0  # Broadcasting creates [N, N]

                n[1]['attention_mask'] = attention_mask
                n[1]['attention_mask_img_shape'] = (latent_height, latent_width)

                combined_conditioning.append(n)

        print(f"   ✅ Generated {len(combined_conditioning)} conditioning blocks\n")

        return (combined_conditioning,)


# Note: These enhanced nodes need the same JavaScript UI as the original nodes
# They will use the canvas interface from MultiAreaConditioning/MultiAreaConditioningMask
