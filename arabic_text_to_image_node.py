"""
ComfyUI - Arabic Professional Text to Image Node
عقدة توليد الصور الاحترافية من النص
Author: Arabic ComfyUI Community
Version: 1.0.0
"""

import torch


# ──────────────────────────────────────────────
#  RESOLUTION PRESETS
# ──────────────────────────────────────────────
RESOLUTION_PRESETS = {
    "Custom (مخصص)":          (0, 0),
    "512 × 512  [Square SD1.5]":  (512,  512),
    "768 × 768  [Square SDXL]":   (768,  768),
    "1024 × 1024 [Square SDXL]":  (1024, 1024),
    "512 × 768  [Portrait SD1.5]":(512,  768),
    "768 × 1024 [Portrait SDXL]": (768,  1024),
    "832 × 1216 [Portrait SDXL]": (832,  1216),
    "1024 × 1344 [Portrait SDXL]":(1024, 1344),
    "768 × 512  [Landscape SD1.5]":(768,  512),
    "1024 × 768 [Landscape SDXL]":(1024, 768),
    "1216 × 832 [Landscape SDXL]":(1216, 832),
    "1344 × 768 [Landscape SDXL]":(1344, 768),
    "1920 × 1080 [Full HD 16:9]": (1920, 1080),
    "1080 × 1920 [Story 9:16]":   (1080, 1920),
    "1280 × 720 [HD 16:9]":       (1280,  720),
    "2048 × 1152 [2K 16:9]":      (2048, 1152),
}

SAMPLER_NAMES = [
    "euler", "euler_ancestral", "heun", "heunpp2",
    "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast",
    "dpm_adaptive", "dpmpp_2s_ancestral", "dpmpp_sde",
    "dpmpp_sde_gpu", "dpmpp_2m", "dpmpp_2m_sde",
    "dpmpp_2m_sde_gpu", "dpmpp_3m_sde", "dpmpp_3m_sde_gpu",
    "ddpm", "lcm", "ddim", "uni_pc", "uni_pc_bh2",
]

SCHEDULER_NAMES = [
    "normal", "karras", "exponential", "sgm_uniform",
    "simple", "ddim_uniform", "beta",
]


# ──────────────────────────────────────────────
#  MAIN NODE CLASS
# ──────────────────────────────────────────────
class ArabicTextToImageNode:
    """
    عقدة توليد الصور الاحترافية من النص  v3
    Professional Arabic Text-to-Image Generation Node

    يدمج هذا النود كل الإعدادات الأساسية في مكان واحد:
      - البرومبيت الإيجابي والسلبي (مع دعم العربية + ترجمة تلقائية للاثنين)
      - معاينة حية للنص المترجم داخل العقدة (عبر JS)
      - أبعاد الصورة (presets + custom)
      - إعدادات KSampler الكاملة
      - Seed مع وضع عشوائي
    """

    TRANSLATION_ENGINES = [
        "online - Google Translate (إنترنت)",
        "offline - Argos Translate (لا إنترنت)",
        "disable - no translation (بدون ترجمة)",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # ── المدخلات الأساسية ──────────────────────────
                "model":  ("MODEL",),
                "clip":   ("CLIP",),
                "vae":    ("VAE",),

                # ── محرك الترجمة (يُطبَّق على كلا البرومبيتين) ──
                "translation_engine": (cls.TRANSLATION_ENGINES, {
                    "default": "online - Google Translate (إنترنت)",
                    "tooltip": "يُطبَّق على البرومبيت الإيجابي والسلبي معاً",
                }),

                # ── البرومبيت الإيجابي ─────────────────────────
                "positive_prompt": ("STRING", {
                    "multiline": True,
                    "default":   "امرأة عربية أنيقة في مدينة مستقبلية، إضاءة سينمائية",
                    "tooltip":   "يمكن الكتابة بالعربية — تُترجَم تلقائياً قبل التوليد",
                }),
                # حقل المعاينة للإيجابي — يملؤه JS تلقائياً
                "pos_translated_preview": ("STRING", {
                    "multiline": True,
                    "default":   "← ستظهر ترجمة البرومبيت الإيجابي هنا",
                    "tooltip":   "معاينة الترجمة الإيجابية (للقراءة فقط)",
                }),

                # ── البرومبيت السلبي ───────────────────────────
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default":   "تشوهات، ضبابية، جودة رديئة، علامة مائية",
                    "tooltip":   "يمكن الكتابة بالعربية — تُترجَم تلقائياً قبل التوليد",
                }),
                # حقل المعاينة للسلبي — يملؤه JS تلقائياً
                "neg_translated_preview": ("STRING", {
                    "multiline": True,
                    "default":   "← ستظهر ترجمة البرومبيت السلبي هنا",
                    "tooltip":   "معاينة الترجمة السلبية (للقراءة فقط)",
                }),

                # ── إعداد الأبعاد ──────────────────────────────
                "resolution_preset": (list(RESOLUTION_PRESETS.keys()), {
                    "default": "768 × 1024 [Portrait SDXL]",
                    "tooltip": "اختر دقة جاهزة أو اختر Custom لتحديد قيم مخصصة",
                }),
                "width": ("INT", {
                    "default": 768, "min": 64, "max": 8192, "step": 64,
                    "tooltip": "عرض الصورة بالبكسل (يُستخدم فقط عند اختيار Custom)",
                }),
                "height": ("INT", {
                    "default": 1024, "min": 64, "max": 8192, "step": 64,
                    "tooltip": "ارتفاع الصورة بالبكسل (يُستخدم فقط عند اختيار Custom)",
                }),

                # ── إعدادات التوليد ────────────────────────────
                "steps": ("INT", {
                    "default": 30, "min": 1, "max": 150, "step": 1,
                    "tooltip": "عدد خطوات التوليد",
                }),
                "cfg": ("FLOAT", {
                    "default": 7.5, "min": 1.0, "max": 30.0, "step": 0.5, "round": 0.01,
                    "tooltip": "قوة الالتزام بالبرومبيت",
                }),
                "sampler_name": (SAMPLER_NAMES, {
                    "default": "dpmpp_2m",
                    "tooltip": "خوارزمية التوليد",
                }),
                "scheduler": (SCHEDULER_NAMES, {
                    "default": "karras",
                    "tooltip": "جدولة الضوضاء",
                }),
                "denoise": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": "1.0 للتوليد الكامل — قيم أقل لـ img2img",
                }),

                # ── Seed ───────────────────────────────────────
                "seed": ("INT", {
                    "default": 42,
                    "min":     0,
                    "max":     0xFFFFFFFFFFFFFFFF,
                    "control_after_generate": "randomize",
                    "tooltip": "رقم البذرة — نفس الرقم يعطي نفس الصورة دائمًا",
                }),
            },
        }

    # ── المخرجات ───────────────────────────────────
    RETURN_TYPES = ("IMAGE", "LATENT", "STRING", "STRING")
    RETURN_NAMES = ("IMAGE",  "LATENT", "positive_translated", "negative_translated")
    FUNCTION     = "generate"
    CATEGORY     = "🎨 Arabic Nodes/Text to Image"
    OUTPUT_NODE  = True

    # ── دالة التوليد الرئيسية ─────────────────────
    def generate(
        self,
        model, clip, vae,
        translation_engine,
        positive_prompt,    pos_translated_preview,
        negative_prompt,    neg_translated_preview,
        resolution_preset,  width, height,
        steps, cfg, sampler_name, scheduler, denoise,
        seed,
    ):
        import comfy.sample
        import latent_preview

        # 1. ترجمة البرومبيتين إذا لزم
        pos_final, pos_status = _translate_text(positive_prompt, translation_engine)
        neg_final, neg_status = _translate_text(negative_prompt, translation_engine)

        # 2. تحديد الأبعاد الفعلية
        preset_w, preset_h = RESOLUTION_PRESETS[resolution_preset]
        final_w = (width  if preset_w == 0 else preset_w) // 64 * 64
        final_h = (height if preset_h == 0 else preset_h) // 64 * 64

        print(f"\n{'='*58}")
        print(f"  🎨 Arabic T2I Node v3 — بدء التوليد")
        print(f"  📐 الدقة  : {final_w} × {final_h}  [{resolution_preset}]")
        print(f"  🔢 Steps  : {steps}  |  CFG: {cfg}  |  Seed: {seed}")
        print(f"  ⚙️  Sampler: {sampler_name}  |  Sched: {scheduler}")
        print(f"  ✅ Pos ({pos_status}): {pos_final[:70]}...")
        print(f"  🚫 Neg ({neg_status}): {neg_final[:70]}...")
        print(f"{'='*58}\n")

        # 3. ترميز النصوص عبر CLIP
        def encode(text):
            tokens = clip.tokenize(text)
            cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            return [[cond, {"pooled_output": pooled}]]

        positive_cond = encode(pos_final)
        negative_cond = encode(neg_final)

        # 4. إنشاء Latent خام
        latent_image = torch.zeros([1, 4, final_h // 8, final_w // 8])

        # 5. تشغيل KSampler
        samples = comfy.sample.sample(
            model,
            noise              = comfy.sample.prepare_noise(latent_image, seed, None),
            steps              = steps,
            cfg                = cfg,
            sampler_name       = sampler_name,
            scheduler          = scheduler,
            positive           = positive_cond,
            negative           = negative_cond,
            latent_image       = latent_image,
            start_step         = 0,
            last_step          = steps,
            force_full_denoise = True,
            denoise            = denoise,
            noise_mask         = None,
            callback           = latent_preview.prepare_callback(model, steps),
            disable_pbar       = False,
            seed               = seed,
        )

        # 6. فك ترميز الـ Latent إلى صورة
        decoded = vae.decode(samples)
        print(f"\n✅ اكتمل التوليد! الحجم: {decoded.shape}")

        return (decoded, {"samples": samples}, pos_final, neg_final)

    @classmethod
    def IS_CHANGED(cls, positive_prompt, negative_prompt, translation_engine, seed, **kwargs):
        import hashlib
        h = hashlib.md5(
            f"{positive_prompt}{negative_prompt}{translation_engine}{seed}".encode()
        ).hexdigest()
        return h


# ──────────────────────────────────────────────
#  TRANSLATION ENGINE  (Online + Offline)
# ──────────────────────────────────────────────
def _translate_text(text: str, engine: str) -> tuple[str, str]:
    """
    يُترجم النص العربي إلى الإنجليزية.
    يُعيد (translated_text, status_message)
    """
    if not text.strip():
        return ("", "⚠️ النص فارغ")

    # ── أوفلاين: Argos Translate ────────────────
    if engine == "offline - Argos Translate (لا إنترنت)":
        try:
            import argostranslate.package
            import argostranslate.translate

            # تحقق هل حزمة ar→en مثبتة
            installed = argostranslate.translate.get_installed_languages()
            codes     = {lang.code for lang in installed}

            if "ar" not in codes or "en" not in codes:
                # تحميل الحزمة تلقائياً (مرة واحدة فقط)
                print("📦 Argos: تحميل حزمة الترجمة ar→en ...")
                argostranslate.package.update_package_index()
                available = argostranslate.package.get_available_packages()
                pkg = next(
                    (p for p in available if p.from_code == "ar" and p.to_code == "en"),
                    None
                )
                if pkg is None:
                    return (text, "❌ Argos: حزمة ar→en غير متوفرة")
                argostranslate.package.install_from_path(pkg.download())
                installed = argostranslate.translate.get_installed_languages()

            ar_lang = next((l for l in installed if l.code == "ar"), None)
            en_lang = next((l for l in installed if l.code == "en"), None)
            if ar_lang is None or en_lang is None:
                return (text, "❌ Argos: اللغات غير متوفرة بعد التثبيت")

            translation = ar_lang.get_translation(en_lang)
            result      = translation.translate(text)
            print(f"✅ Argos Offline → {result}")
            return (result, "✅ ترجمة أوفلاين (Argos)")

        except ImportError:
            return (text, "❌ argostranslate غير مثبتة — نفّذ: pip install argostranslate")
        except Exception as e:
            return (text, f"❌ Argos خطأ: {e}")

    # ── أونلاين: deep-translator (Google) ───────
    elif engine == "online - Google Translate (إنترنت)":
        try:
            from deep_translator import GoogleTranslator
            result = GoogleTranslator(source="auto", target="en").translate(text)
            print(f"✅ Google → {result}")
            return (result, "✅ ترجمة أونلاين (Google)")
        except ImportError:
            return (text, "❌ deep-translator غير مثبتة — نفّذ: pip install deep-translator")
        except Exception as e:
            return (text, f"❌ Google خطأ: {e}")

    # ── بدون ترجمة ──────────────────────────────
    else:
        return (text, "ℹ️ الترجمة معطلة")


# ──────────────────────────────────────────────
#  HELPER NODE: Prompt Builder  v2
# ──────────────────────────────────────────────
class ArabicPromptBuilderNode:
    """
    مساعد بناء البرومبيت الاحترافي
    • ترجمة أونلاين  → Google Translate (deep-translator)
    • ترجمة أوفلاين → Argos Translate  (بدون إنترنت)
    • معاينة حية للنص المترجم داخل العقدة عبر JavaScript
    """

    QUALITY_TAGS = {
        "Ultra Quality (جودة فائقة)": "masterpiece, best quality, ultra-detailed, 8k uhd",
        "Cinematic (سينمائي)":        "cinematic lighting, film grain, dramatic shadows",
        "Photography (تصوير فوتوغرافي)": "professional photography, sharp focus, DSLR",
        "Digital Art (فن رقمي)":     "digital art, concept art, artstation trending",
        "Anime Style (أنمي)":         "anime style, manga, studio ghibli",
        "Oil Painting (لوحة زيتية)":  "oil painting, classical art, brushstroke texture",
    }

    TRANSLATION_ENGINES = [
        "online - Google Translate (إنترنت)",
        "offline - Argos Translate (لا إنترنت)",
        "disable - no translation (بدون ترجمة)",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "subject": ("STRING", {
                    "multiline": True,
                    "default":   "امرأة عربية في واحة",
                    "tooltip":   "الموضوع الرئيسي — يُترجم تلقائياً",
                }),
                "environment": ("STRING", {
                    "multiline": False,
                    "default":   "غروب الشمس، نخل، رمال ذهبية",
                    "tooltip":   "البيئة والخلفية — يُترجم تلقائياً",
                }),
                "style_quality": (list(cls.QUALITY_TAGS.keys()), {
                    "default": "Ultra Quality (جودة فائقة)",
                }),
                "translation_engine": (cls.TRANSLATION_ENGINES, {
                    "default": "online - Google Translate (إنترنت)",
                    "tooltip": "اختر محرك الترجمة",
                }),
                "extra_tags": ("STRING", {
                    "multiline": True,
                    "default":   "",
                    "tooltip":   "كلمات مفتاحية إنجليزية إضافية تُضاف بعد الترجمة",
                }),
                # حقل المعاينة — يملؤه JavaScript تلقائياً، ويُستخدم أيضاً كوسيلة عرض
                "translated_preview": ("STRING", {
                    "multiline": True,
                    "default":   "← سيظهر النص المترجم هنا تلقائياً",
                    "tooltip":   "معاينة فورية للنص بعد الترجمة (للقراءة فقط)",
                }),
            }
        }

    RETURN_TYPES  = ("STRING", "STRING", "STRING")
    RETURN_NAMES  = ("prompt_output", "original_arabic", "translation_status")
    FUNCTION      = "build"
    CATEGORY      = "🎨 Arabic Nodes/Text to Image"

    # ── دالة البناء الرئيسية ──────────────────────
    def build(
        self,
        subject, environment,
        style_quality, translation_engine,
        extra_tags, translated_preview,
    ):
        quality_tag   = self.QUALITY_TAGS[style_quality]
        arabic_parts  = [p.strip() for p in [subject, environment] if p.strip()]
        combined_arabic = ", ".join(arabic_parts)

        print(f"\n{'─'*50}")
        print(f"  ✍️  Arabic Prompt Builder v2")
        print(f"  📝 النص العربي: {combined_arabic}")
        print(f"  ⚙️  المحرك: {translation_engine}")

        # الترجمة
        translated, status = _translate_text(combined_arabic, translation_engine)

        # بناء البرومبيت النهائي
        parts = [p for p in [translated, quality_tag, extra_tags] if p.strip()]
        final_prompt = ", ".join(parts)

        print(f"  🌐 الترجمة: {translated}")
        print(f"  🚀 البرومبيت النهائي: {final_prompt}")
        print(f"  {status}")
        print(f"{'─'*50}\n")

        return (final_prompt, combined_arabic, status)

    @classmethod
    def IS_CHANGED(cls, subject, environment, translation_engine, **kwargs):
        # إعادة تشغيل عند تغيير النص أو المحرك
        import hashlib
        h = hashlib.md5(f"{subject}{environment}{translation_engine}".encode()).hexdigest()
        return h
