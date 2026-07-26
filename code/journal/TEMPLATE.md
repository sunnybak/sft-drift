<!--
Copy this to journal/NNNN-YYYY-MM-DD-slug.md (zero-padded, next number).
Keep it under ~1000 words: skimmable > exhaustive. The git log + result files
hold the detail; this holds the story and the state. Delete these HTML comments.
-->
# Session NNNN — YYYY-MM-DD — <one-line title>

**Agent:** <model> · **Box:** <gpu, e.g. Vast RTX 4090> · **Commits:** `<first>..<last>`

## State now (read this first)
<2–4 sentences. Where the project actually is: what's done and trustworthy,
the current headline result, and anything half-finished or on fire. Written for
someone who has read CLAUDE.md but nothing else.>

## What happened
<Bullets, roughly chronological. Reference commits by hash. One line each.>
- …

## Key numbers & where they live
<The results that matter + the file path to find them. Tables fine. Always cite
the file so the next agent can re-read, not just trust this summary.>
- … → `results/<file>`

## Landmines & tips (spend the next agent's time well)
<What bit us / wasted time / is non-obvious. What NOT to redo. Which outputs are
BROKEN and superseded. New gotchas not yet in CLAUDE.md — and if it's a durable
one, also add it to CLAUDE.md and say so here.>
- …

## Reproduce / main scripts
<The commands that regenerate the above, in order. Note runtimes & GPU needs.>
```bash
…
```

## Next session — suggested (prioritized)
<Ranked. For each: what, why, and any risk/blocker. Mark anything BLOCKED on the
human. Flag durability chores (adapters synced? box safe to destroy?).>
1. …
