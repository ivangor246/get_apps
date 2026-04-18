> **Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## About

A pipeline tool for collecting and processing app data from app stores.

**Two core concerns:**
1. **Collection** — crawl store catalogues by category, extract app identifiers, persist raw results.
2. **Processing** — analyze and transform the collected data (reporting, filtering, enrichment, etc.)

These concerns are intentionally decoupled: collection produces raw output files; processing reads them independently.

## Tech Stack

- **Python 3.14+**, async throughout (`asyncio`)
- **Playwright** — headless browser automation (anti-bot bypass, JS rendering)
- **BeautifulSoup + lxml** — HTML parsing
- **Poetry** — dependency management
- **Ruff** — linting and formatting

## Folder Structure

```
src/app/
├── main.py           # Entry point
├── core/             # Config, custom exceptions, etc.
├── tasks/            # High-level orchestration per store
└── services/
    ├── *.py          # Service classes (one per store)
    └── parsers/      # Low-level HTML parsers (one per store)
    ...               # Other layers as needed

saved_data/
└── categories/
    └── {timestamp}/  # One directory per run
        └── *.txt     # One file per category
    ...               # Other data as needed
```

## Architecture

The system is split into three layers:

1. **Tasks** — entry points per store; wired in `main.py`. Each task runs an independent collection pipeline.
2. **Services** — orchestrate a full collection run: browser lifecycle, pagination, concurrency, output writing.
3. **Parsers** — fetch a single page via Playwright, extract app identifiers with BeautifulSoup.

**Adding a new store** = add a parser, a service, and a task. No changes to existing code.

---

## Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

---

## Code Style

Write professional, idiomatic code consistent with the language and ecosystem.

- Follow language-standard conventions (PEP 8, Effective Go, Airbnb JS, etc.).
- Use clear, descriptive names for variables, functions, and classes.
- Prefer explicit over implicit.
- Consistency with existing code overrides personal preference.

---

## Comments & Documentation

**Comments** — only when necessary. Never explain the obvious.
Good comment: *why* the code does something non-obvious.
Bad comment: restating what the code already says.

**Docstrings / JSDoc / etc.** — required for every class, method, and function.
- Maximum 3 lines: purpose, key params/returns if non-obvious, notable caveats.
- Do not document anything else (variables, modules, type aliases, etc.).

---

## Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

> Ask yourself: *"Would a senior engineer say this is overcomplicated?"* If yes, simplify.

---

## Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports / variables / functions that **your** changes made unused.
- Don't remove pre-existing dead code unless asked.

> **The test:** Every changed line should trace directly to the user's request.

---

## Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass."
- "Fix the bug" → "Write a test that reproduces it, then make it pass."
- "Refactor X" → "Ensure tests pass before and after."

For multi-step tasks, state a brief plan before starting:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Weak success criteria ("make it work") require constant clarification — avoid them.

---

## Git

- **Never run git commands** (commit, push, rebase, etc.) without an explicit user request.
- At the end of every response that changes code, provide a short suggested commit message in a code block:

```
feat: add JWT refresh token rotation
```

---

## Error Handling

- Handle errors at the boundary where recovery or user feedback is meaningful.
- Don't swallow errors silently.
- Don't add error handling for states that cannot occur given the current design.

---

## Security & Safety

- Never hard-code secrets, API keys, or credentials — use environment variables.
- Validate and sanitize all external input (user, API, file).
- Prefer well-maintained libraries over custom crypto or auth implementations.
- Flag security concerns explicitly rather than silently working around them.
