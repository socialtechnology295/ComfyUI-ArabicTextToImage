"""
ComfyUI - Arabic Text to Image Node Pack  v2
عقدة توليد الصور الاحترافية من النص
"""

from .arabic_text_to_image_node import (
    ArabicTextToImageNode,
    ArabicPromptBuilderNode,
    _translate_text,
)

# ─── تسجيل العقد مع ComfyUI ───────────────────────────────────────────────────
NODE_CLASS_MAPPINGS = {
    "ArabicTextToImage":   ArabicTextToImageNode,
    "ArabicPromptBuilder": ArabicPromptBuilderNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArabicTextToImage":   "🎨 Arabic Text to Image  |  توليد الصور من النص",
    "ArabicPromptBuilder": "✍️  Arabic Prompt Builder  |  بناء البرومبيت + ترجمة",
}

# مجلد JavaScript للمعاينة الحية
WEB_DIRECTORY = "./web"


# ─── API Route: /arabic_translate ──────────────────────────────────────────────
try:
    from aiohttp import web
    from server import PromptServer

    @PromptServer.instance.routes.post("/arabic_translate")
    async def arabic_translate_api(request):
        """
        POST /arabic_translate
        Body JSON: { "text": "...", "engine": "..." }
        Response:  { "translated": "...", "status": "..." }
        """
        try:
            data       = await request.json()
            text       = data.get("text", "").strip()
            engine     = data.get("engine", "online - Google Translate (إنترنت)")

            if not text:
                return web.json_response({"translated": "", "status": "⚠️ نص فارغ"})

            translated, status = _translate_text(text, engine)
            return web.json_response({"translated": translated, "status": status})

        except Exception as e:
            return web.json_response(
                {"translated": "", "status": f"❌ خطأ: {e}"},
                status=500,
            )

    print("  🌐 API مُفعَّل: POST /arabic_translate")

except Exception as e:
    print(f"  ⚠️ تعذّر تسجيل API الترجمة: {e}")


# ─── رسالة التحميل ─────────────────────────────────────────────────────────────
print("\n" + "═" * 60)
print("  🎨 Arabic Text to Image Node Pack v2  |  تم التحميل")
print("  ✅ العقد المسجلة:")
print("     → 🎨 Arabic Text to Image")
print("     → ✍️  Arabic Prompt Builder  (أونلاين + أوفلاين + معاينة حية)")
print("  📦 المكتبات:")
print("     pip install deep-translator   # الترجمة الأونلاين")
print("     pip install argostranslate    # الترجمة الأوفلاين")
print("═" * 60 + "\n")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
