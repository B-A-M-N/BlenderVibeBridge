# 🏗️ Contributing to the Iron Box

> [!IMPORTANT]
> **READ THIS BEFORE OPENING A PULL REQUEST.**
> We do not accept "vibes-based" code. This is a governed state machine operating on destructive Blender endpoints. Your code must be **defensive, typed, and paranoid.**

## ⚔️ The Code Philosophy: "Zero Trust"

We operate under a simple axiom: **The Blender Engine is hostile.** It wants to crash, it wants to hang, and it wants to corrupt user data. Your code is the shield.

1.  **No "Happy Paths"**: Assume the socket is dead, the object is null, and the user is spamming the button. Handle the edge case first.
2.  **Explicit > Implicit**: No magic. If a function mutates state, it must return a clear result or error.
3.  **Performance is a Feature**: We operate in the main thread timer. Heavy allocations or blocking calls are rejected.

---

## 🏛️ Language Standards: Python

*The chaotic script environment. Must be disciplined.*

*   **Formatter**: `Black` (Line length: 88).
*   **Linter**: `Ruff` or `Flake8`.
*   **Type Hinting**: **MANDATORY**. All function signatures must have type hints.
*   **Blender Context**:
    *   Never assume `bpy.context` is correct. Use context overrides.
    *   Wrap all `bpy.ops` in `try/except` blocks.
*   **Modularity**: All new mutations must be registered in the `ModelingKernel._dispatch` registry.

---

## 🛡️ The Gauntlet (PR Requirements)

Before submitting, verify your code survives **The Gauntlet**:

1.  **The "Destruction" Test**: What happens if Blender is force-closed during your function?
2.  **The "Spam" Test**: What happens if the AI calls your tool 50 times in 1 second?
3.  **Verification**: Every mutation must include a post-check to prove reality matches intent.

---

## 📜 Legal & DCO

By contributing, you grant the Author (**B-A-M-N**) a perpetual, irrevocable license to use and sublicense your contributions under the project's **Dual-License (AGPLv3/Commercial)** model.

**Sign-off Procedure**:
All commits must be signed off to certify the Developer Certificate of Origin (DCO).

```bash
git commit -s -m "feat: implement atomic mesh cleanup"
```

**Welcome to the Iron Box. Build it strong.**