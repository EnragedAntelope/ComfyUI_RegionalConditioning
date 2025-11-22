# ComfyUI Regional Conditioning

Control different parts of your image with separate prompts using visual box drawing.

## Quick Start

1. **Install**: Clone to `ComfyUI/custom_nodes/` or use ComfyUI Manager
2. **Add Node**: Search for "Regional Prompter"
3. **Connect**: CLIP → Regional Prompter → Sampler
4. **Draw**: Use canvas to position regions, type prompts
5. **Generate**: Connect to your sampler and run

## Nodes

### Regional Prompter (Mask-Based)
**For:** Flux, Chroma, SD3, SD3.5, Qwen-Image

**Inputs:**
- `clip`: CLIP from checkpoint
- `width`/`height`: Must match your latent dimensions
- `soften_masks`: Feathering at edges (recommended ON)
- `background_prompt`: Scene description
- `region1-4_prompt`: Region-specific prompts

**Tips:**
- Use CFG 1.0-3.5 with Flux (higher = blur)
- Keep to 3-4 regions max for Flux/Chroma
- Default strength 0.8 works well

### Regional Prompter (Area-Based)
**For:** SD1.5, SD2.x, SDXL

Same interface, uses area-based conditioning instead of masks.

## Canvas Controls

- **index**: Select which region to edit
- **box_x, box_y**: Region top-left position
- **box_w, box_h**: Region dimensions
- **strength**: Conditioning strength (0-10, default 0.8)

## Example Workflow

```
Checkpoint Loader
├→ CLIP → Regional Prompter (Mask-Based)
│           ├ width: 1024
│           ├ height: 1024
│           ├ soften_masks: true
│           ├ background: "city street"
│           ├ region1: "red sports car"
│           └ region2: "street vendor"
├→ MODEL → KSampler ← conditioning
└→ VAE → VAE Decode
```

## Troubleshooting

**Regions not showing:**
- Check width/height match your latent exactly
- Try lower CFG (1.0-2.0) with Flux
- Verify boxes aren't outside image bounds

**Validation errors:**
- Ensure width/height are multiples of 64
- Check no regions overlap fullscreen

**Blurry output:**
- Lower CFG (Flux likes 1.0-3.5)
- Try strength 0.6-0.8 instead of 1.0

## Advanced Nodes

Original nodes available for complex workflows:

- **Multi Area Conditioning**: Area-based, requires external CLIP encode
- **Multi Area Conditioning Mask**: Mask-based, requires external CLIP encode
- **Multi Latent Composite**: Visual latent compositing with feathering

## Credits

Based on visual area conditioning by [Davemane42](https://github.com/Davemane42).

Maintained by EnragedAntelope - [github.com/EnragedAntelope/ComfyUI_RegionalConditioning](https://github.com/EnragedAntelope/ComfyUI_RegionalConditioning)

## License

MIT License - use freely in personal and commercial projects.
