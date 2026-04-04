// socrates.ts
//
// Purpose: Core Socrates logic — debounce, question fetching, submit streaming, rendering
//
// This module:
// - Exports a generic debounce utility
// - Fetches ranked clarifying questions from the API
// - Streams extended reasoning responses via SSE
// - Renders question lists into a DOM container

export interface Question {
    priority: string;
    question: string;
}

export function debounce<T extends (...args: unknown[]) => void>(fn: T, ms: number): T {
    let timer: ReturnType<typeof setTimeout>;
    return ((...args: Parameters<T>) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), ms);
    }) as T;
}

export async function fetchQuestions(
    prompt: string,
    model: string,
    base = ""
): Promise<Question[]> {
    if (prompt.trim().length < 10) return [];
    try {
        const res = await fetch(`${base}/api/questions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt, model }),
        });
        const data = (await res.json()) as { questions: Question[] };
        return data.questions ?? [];
    } catch {
        return [];
    }
}

export async function* streamSubmit(
    prompt: string,
    model: string,
    base = ""
): AsyncGenerator<string> {
    const res = await fetch(`${base}/api/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, model }),
    });

    const reader = res.body?.getReader();
    if (!reader) return;

    const dec = new TextDecoder();
    let buf = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buf += dec.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() ?? "";

        for (const line of lines) {
            if (!line.startsWith("data: ") || line.includes("[DONE]")) continue;
            try {
                const { token } = JSON.parse(line.slice(6)) as { token: string };
                if (token) yield token;
            } catch {
                // skip malformed chunk
            }
        }
    }
}

export function renderQuestions(questions: Question[], el: HTMLElement): void {
    if (!questions.length) {
        el.innerHTML = `<span class="hint">Start typing to see clarifying questions…</span>`;
        return;
    }
    el.innerHTML = questions
        .map(
            (q) =>
                `<div class="question">
                    <span class="priority priority-${q.priority}">${q.priority}</span>
                    <span class="question-text">${q.question}</span>
                </div>`
        )
        .join("");
}
