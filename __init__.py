"""
ComfyUI - Arabic Text to Image Node Pack v2
Professional Arabic-to-Image Generation Nodes
"""

from .arabic_text_to_image_node import (
    ArabicTextToImageNode,
    ArabicPromptBuilderNode,
    _translate_text,
)

# ─────────────────────────────────────────────────────────────
# Register Nodes with ComfyUI
# ─────────────────────────────────────────────────────────────
NODE_CLASS_MAPPINGS = {
    "ArabicTextToImage":   ArabicTextToImageNode,
    "ArabicPromptBuilder": ArabicPromptBuilderNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArabicTextToImage":   "Arabic Text to Image",
    "ArabicPromptBuilder": "Arabic Prompt Builder",
}

# Optional Web UI directory
WEB_DIRECTORY = "./web"


# ─────────────────────────────────────────────────────────────
# API Route: /arabic_translate
# ─────────────────────────────────────────────────────────────
try:
    from aiohttp import web
    from server import PromptServer

    @PromptServer.instance.routes.post("/arabic_translate")
    async def arabic_translate_api(request):
        """
        POST /arabic_translate
        Body JSON:
        {
            "text": "...",
            "engine": "..."
        }

        Response:
        {
            "translated": "...",
            "status": "..."
        }
        """
        try:
            data   = await request.json()
            text   = data.get("text", "").strip()
            engine = data.get("engine", "online - Google Translate")

            if not text:
                return web.json_response({
                    "translated": "",
                    "status": "Empty input text"
                })

            translated, status = _translate_text(text, engine)

            return web.json_response({
                "translated": translated,
                "status": status
            })

        except Exception as e:
            return web.json_response(
                {
                    "translated": "",
                    "status": f"Error: {str(e)}"
                },
                status=500,
            )

    print("Arabic Text to Image: Translation API registered at /arabic_translate")

except Exception as e:
    print(f"Arabic Text to Image: Failed to register translation API: {e}")


# ─────────────────────────────────────────────────────────────
# Load Message
# ─────────────────────────────────────────────────────────────
print("=" * 60)
print("Arabic Text to Image Node Pack v2 loaded successfully.")
print("Registered nodes:")
print("  - Arabic Text to Image")
print("  - Arabic Prompt Builder")
print("Optional dependencies:")
print("  pip install deep-translator   # Online translation")
print("  pip install argostranslate    # Offline translation")
print("=" * 60)


__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
