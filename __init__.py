# ComfyUI Regional Conditioning
# Enhanced nodes with inline prompts for easy regional control

from .RegionalPrompting import (
    RegionalPrompterSimple,
    RegionalPrompterFlux
)

NODE_CLASS_MAPPINGS = {
    "RegionalPrompterSimple": RegionalPrompterSimple,
    "RegionalPrompterFlux": RegionalPrompterFlux,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RegionalPrompterSimple": "Regional Prompter (Area-Based)",
    "RegionalPrompterFlux": "Regional Prompter (Mask-Based)",
}

# Export web directory for JavaScript files
import os
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "js")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

print('\033[34mComfyUI_RegionalConditioning: \033[92mLoaded successfully\033[0m')
