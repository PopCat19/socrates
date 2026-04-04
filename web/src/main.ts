// main.ts
//
// Purpose: Web UI entry point — wires model selector, debounced input, and Ctrl+Enter submit
//
// This module:
// - Fetches models on load; falls back to text input if unavailable
// - Triggers question generation with 400ms debounce on prompt changes
// - Streams extended reasoning response on Ctrl+Enter

import { debounce, fetchQuestions, renderQuestions, streamSubmit } from "./socrates";

let currentModel = "";

async function initModel(): Promise<void> {
    const sel = document.getElementById("model-selector") as HTMLSelectElement;
    const inp = document.getElementById("model-input") as HTMLInputElement;

    try {
        const res = await fetch("/api/models");
        const { models } = (await res.json()) as { models: string[] };

        if (!models.length) throw new Error("empty");

        sel.innerHTML = models.map((m) => `<option value="${m}">${m}</option>`).join("");
        sel.style.display = "block";
        inp.style.display = "none";
        currentModel = models[0];
        sel.addEventListener("change", () => {
            currentModel = sel.value;
        });
    } catch {
        sel.style.display = "none";
        inp.style.display = "block";
        currentModel = inp.value;
        inp.addEventListener("input", () => {
            currentModel = inp.value.trim();
        });
    }
}

async function main(): Promise<void> {
    await initModel();

    const prompt = document.getElementById("prompt") as HTMLTextAreaElement;
    const questionsEl = document.getElementById("questions")!;
    const responseEl = document.getElementById("response")!;

    const onType = debounce(async () => {
        const questions = await fetchQuestions(prompt.value, currentModel);
        renderQuestions(questions, questionsEl);
    }, 400);

    prompt.addEventListener("input", onType);

    prompt.addEventListener("keydown", async (e) => {
        if (!(e.key === "Enter" && e.ctrlKey)) return;
        e.preventDefault();

        responseEl.textContent = "";
        responseEl.classList.add("streaming");

        for await (const token of streamSubmit(prompt.value, currentModel)) {
            responseEl.textContent += token;
            responseEl.scrollTop = responseEl.scrollHeight;
        }

        responseEl.classList.remove("streaming");
    });

    const sidebar = document.getElementById("sidebar")!;
    const overlay = document.getElementById("sidebarOverlay")!;
    const menuBtn = document.getElementById("menuBtn")!;
    const fabBtn = document.getElementById("fabBtn")!;

    menuBtn.addEventListener("click", () => {
        sidebar.classList.toggle("open");
        overlay.classList.toggle("show");
        document.body.classList.toggle("no-scroll");
    });

    overlay.addEventListener("click", () => {
        sidebar.classList.remove("open");
        overlay.classList.remove("show");
        document.body.classList.remove("no-scroll");
    });

    fabBtn.addEventListener("click", () => {
        const event = new KeyboardEvent("keydown", { key: "Enter", ctrlKey: true });
        prompt.dispatchEvent(event);
    });
}

main();
