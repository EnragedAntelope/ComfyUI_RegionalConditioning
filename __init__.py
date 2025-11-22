# Made by Davemane42#0042 for ComfyUI
# Modernized for ComfyUI 0.3.71+ compatibility
# Enhanced version with inline prompts - November 2025

from .MultiAreaConditioning import (
    MultiAreaConditioning,
    MultiAreaConditioningMask,
    ConditioningUpscale,
    ConditioningStretch,
    ConditioningDebug
)
from .MultiLatentComposite import MultiLatentComposite
from .RegionalPrompting import (
    RegionalPrompterSimple,
    RegionalPrompterFlux
)

NODE_CLASS_MAPPINGS = {
    # Original nodes (require external CLIP Text Encode)
    "MultiLatentComposite": MultiLatentComposite,
    "MultiAreaConditioning": MultiAreaConditioning,
    "MultiAreaConditioningMask": MultiAreaConditioningMask,
    "ConditioningUpscale": ConditioningUpscale,
    "ConditioningStretch": ConditioningStretch,

    # Enhanced all-in-one nodes (inline prompts - RECOMMENDED)
    "RegionalPrompterSimple": RegionalPrompterSimple,
    "RegionalPrompterFlux": RegionalPrompterFlux,
}

# Display names for the UI
NODE_DISPLAY_NAME_MAPPINGS = {
    # Original nodes
    "MultiLatentComposite": "Multi Latent Composite (Visual)",
    "MultiAreaConditioning": "Multi Area Conditioning (SD1.5/SDXL)",
    "MultiAreaConditioningMask": "Multi Area Conditioning (Mask-Based)",
    "ConditioningUpscale": "Conditioning Upscale",
    "ConditioningStretch": "Conditioning Stretch",

    # Enhanced nodes with inline prompts
    "RegionalPrompterSimple": "Regional Prompter (Area-Based)",
    "RegionalPrompterFlux": "Regional Prompter (Mask-Based)",
}

# Export web directory for JavaScript files
import os
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "js")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

print('\033[34mComfyUI_RegionalConditioning: \033[92mLoaded successfully\033[0m')
