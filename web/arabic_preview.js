/**
 * Arabic Nodes — Live Translation Preview  v3
 * معاينة الترجمة الحية لعقدتَي ArabicTextToImage و ArabicPromptBuilder
 *
 * الميزات:
 *  ① عقدة ArabicTextToImage:
 *     - مربع معاينة خضراء للبرومبيت الإيجابي المترجَم
 *     - مربع معاينة حمراء للبرومبيت السلبي  المترجَم
 *     - كلاهما يتحدث فور الكتابة (debounce 800ms)
 *
 *  ② عقدة ArabicPromptBuilder:
 *     - مربع معاينة واحد للنص المدمج بعد الترجمة
 *
 *  المشترك:
 *     - مؤشر حالة (⏳ / ✅ / ❌ / ℹ️)
 *     - زر ⎘ نسخ لكل مربع
 *     - لا طلبات مكررة (cache بسيط بالنص + المحرك)
 */

import { app } from "../../scripts/app.js";

// ═══════════════════════════════════════════════
//  ثوابت
// ═══════════════════════════════════════════════
const API          = "/arabic_translate";
const DEBOUNCE_MS  = 800;

// ═══════════════════════════════════════════════
//  مصنع بناء مربع المعاينة
//  accent: لون الحدود / الكتابة  (#2a6a4a أخضر | #6a2a2a أحمر)
// ═══════════════════════════════════════════════
function makePreviewBox(accentHex, labelText) {
  const dim    = accentHex;          // لون الحدود
  const bright = accentHex + "cc";  // لون النص (أفتح)

  const box = document.createElement("div");
  box.style.cssText = `
    background:#0d1117;
    border:1px solid ${dim};
    border-radius:6px;
    padding:8px 10px;
    margin-top:4px;
    font-family:'Consolas',monospace;
    font-size:11px;
    line-height:1.55;
    word-break:break-word;
    position:relative;
    min-height:40px;
  `;

  box.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
      <span style="font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:${dim};">
        ${labelText}
      </span>
      <span class="arb-status" style="font-size:9px;color:#666;font-style:italic;">
        — في انتظار النص —
      </span>
    </div>
    <div class="arb-text" style="color:#444;font-style:italic;">
      اكتب لرؤية الترجمة...
    </div>
    <button class="arb-copy" style="
      position:absolute;top:6px;right:6px;
      background:${dim}22;border:1px solid ${dim};border-radius:4px;
      color:${dim};font-size:10px;padding:2px 7px;
      cursor:pointer;transition:background .15s;
    ">⎘ نسخ</button>
  `;

  const statusEl = box.querySelector(".arb-status");
  const textEl   = box.querySelector(".arb-text");
  const copyBtn  = box.querySelector(".arb-copy");

  copyBtn.addEventListener("click", () => {
    const t = textEl.textContent.trim();
    if (t && !t.startsWith("اكتب")) {
      navigator.clipboard.writeText(t).then(() => {
        copyBtn.textContent = "✅ تم";
        setTimeout(() => (copyBtn.textContent = "⎘ نسخ"), 1500);
      });
    }
  });

  // API: تحديث المحتوى
  const api = {
    setLoading() {
      statusEl.textContent   = "⏳ يترجم...";
      textEl.textContent     = "...";
      textEl.style.color     = "#555";
      textEl.style.fontStyle = "italic";
    },
    setDisabled(raw) {
      statusEl.textContent   = "ℹ️ معطلة";
      textEl.textContent     = raw || "—";
      textEl.style.color     = "#666";
      textEl.style.fontStyle = "normal";
    },
    setEmpty() {
      statusEl.textContent   = "— في انتظار النص —";
      textEl.textContent     = "اكتب لرؤية الترجمة...";
      textEl.style.color     = "#444";
      textEl.style.fontStyle = "italic";
    },
    setResult(translated, status) {
      textEl.textContent     = translated;
      textEl.style.color     = bright;
      textEl.style.fontStyle = "normal";
      statusEl.textContent   = status ?? "✅ تمت الترجمة";
    },
    setError(msg) {
      textEl.textContent     = msg;
      textEl.style.color     = "#e05050";
      textEl.style.fontStyle = "italic";
      statusEl.textContent   = "❌ فشل";
    },
    getText: () => textEl.textContent,
  };

  return { el: box, api };
}

// ═══════════════════════════════════════════════
//  دالة الترجمة عبر API
// ═══════════════════════════════════════════════
async function fetchTranslation(text, engine) {
  try {
    const r = await fetch(API, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text, engine }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const d = await r.json();
    return { ok: true, text: d.translated, status: d.status };
  } catch (e) {
    return { ok: false, text: "", status: `❌ ${e.message}` };
  }
}

// ═══════════════════════════════════════════════
//  مساعد: إنشاء منطق debounce + cache لمربع واحد
// ═══════════════════════════════════════════════
function makeTranslator(boxApi, getSource, getEngine, hiddenWidget, node) {
  let timer   = null;
  let lastKey = "";

  async function run() {
    const engine  = getEngine();
    const text    = getSource().trim();

    if (!text) { boxApi.setEmpty(); return; }

    if (engine.startsWith("disable")) {
      boxApi.setDisabled(text);
      if (hiddenWidget) hiddenWidget.value = text;
      return;
    }

    const key = `${text}||${engine}`;
    if (key === lastKey) return;
    lastKey = key;

    boxApi.setLoading();
    const res = await fetchTranslation(text, engine);

    if (res.ok && res.text) {
      boxApi.setResult(res.text, res.status);
      if (hiddenWidget) hiddenWidget.value = res.text;
    } else {
      boxApi.setError(res.status);
      if (hiddenWidget) hiddenWidget.value = "";
    }
    node.setDirtyCanvas(true, true);
  }

  return {
    schedule() {
      clearTimeout(timer);
      timer = setTimeout(run, DEBOUNCE_MS);
    },
    runNow: run,
  };
}

// ═══════════════════════════════════════════════
//  تسجيل الامتداد
// ═══════════════════════════════════════════════
app.registerExtension({
  name: "ArabicNodes.LiveTranslationPreview.v3",

  async nodeCreated(node) {
    const cls = node.comfyClass;

    // ── مساعد إيجاد widget ──────────────────────
    const w = (name) => node.widgets?.find((x) => x.name === name);

    // ════════════════════════════════════════════
    //  عقدة ArabicTextToImage — إيجابي + سلبي
    // ════════════════════════════════════════════
    if (cls === "ArabicTextToImage") {
      const engineW  = w("translation_engine");
      const posW     = w("positive_prompt");
      const negW     = w("negative_prompt");
      const posPrevW = w("pos_translated_preview");
      const negPrevW = w("neg_translated_preview");

      if (!engineW || !posW || !negW) return;

      // أخفِ حقلَي المعاينة الأصليين
      [posPrevW, negPrevW].forEach((x) => {
        if (x) x.computeSize = () => [0, -4];
      });

      // ── مربع الإيجابي (أخضر) ──────────────────
      const pos = makePreviewBox("#2a7a4a", "✅ الإيجابي — Positive Translated");
      node.addDOMWidget("arb_pos_preview", "div", pos.el, {
        getValue:       () => pos.api.getText(),
        setValue:       (v) => {},
        computeSize:    () => [node.size[0], 72],
        serializeValue: false,
      });

      // ── مربع السلبي (أحمر) ────────────────────
      const neg = makePreviewBox("#7a2a2a", "🚫 السلبي — Negative Translated");
      node.addDOMWidget("arb_neg_preview", "div", neg.el, {
        getValue:       () => neg.api.getText(),
        setValue:       (v) => {},
        computeSize:    () => [node.size[0], 72],
        serializeValue: false,
      });

      // ── منطق الترجمة ──────────────────────────
      const getEngine = () => engineW.value ?? "";

      const posTr = makeTranslator(
        pos.api,
        () => posW.value ?? "",
        getEngine,
        posPrevW,
        node,
      );
      const negTr = makeTranslator(
        neg.api,
        () => negW.value ?? "",
        getEngine,
        negPrevW,
        node,
      );

      // ── ربط أحداث تغيير الـ widgets ────────────
      const origCb = node.onWidgetChanged?.bind(node);
      node.onWidgetChanged = function (name, value, oldValue, widget) {
        origCb?.(name, value, oldValue, widget);
        if (name === "positive_prompt"    || name === "translation_engine") posTr.schedule();
        if (name === "negative_prompt"    || name === "translation_engine") negTr.schedule();
      };

      // تشغيل أولي
      setTimeout(() => { posTr.runNow(); negTr.runNow(); }, 400);
    }

    // ════════════════════════════════════════════
    //  عقدة ArabicPromptBuilder — مربع واحد
    // ════════════════════════════════════════════
    if (cls === "ArabicPromptBuilder") {
      const subjectW = w("subject");
      const envW     = w("environment");
      const engineW  = w("translation_engine");
      const prevW    = w("translated_preview");

      if (!subjectW || !engineW) return;
      if (prevW) prevW.computeSize = () => [0, -4];

      const box = makePreviewBox("#2a5a7a", "🌐 معاينة الترجمة");
      node.addDOMWidget("arb_builder_preview", "div", box.el, {
        getValue:       () => box.api.getText(),
        setValue:       (v) => {},
        computeSize:    () => [node.size[0], 72],
        serializeValue: false,
      });

      const getCombined = () =>
        [subjectW.value ?? "", envW?.value ?? ""]
          .map((s) => s.trim())
          .filter(Boolean)
          .join("، ");

      const tr = makeTranslator(
        box.api,
        getCombined,
        () => engineW.value ?? "",
        prevW,
        node,
      );

      const origCb = node.onWidgetChanged?.bind(node);
      node.onWidgetChanged = function (name, value, oldValue, widget) {
        origCb?.(name, value, oldValue, widget);
        if (["subject", "environment", "translation_engine"].includes(name)) {
          tr.schedule();
        }
      };

      setTimeout(tr.runNow, 400);
    }
  },
});
