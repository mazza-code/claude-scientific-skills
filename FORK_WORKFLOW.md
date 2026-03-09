# Fork Maintenance Workflow

This fork tracks upstream `K-Dense-AI/claude-scientific-skills` while keeping local hardening fixes on:

- Branch: `codex/fixes-skill-hardening-2026-03-09`
- Tag: `mazza-skills-fixes-2026-03-09`

## Daily use (install pinned skills in Codex)

Use the pinned tag when installing skills so your local setup is reproducible:

```bash
python /Users/mazza/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo mazza-code/claude-scientific-skills \
  --ref mazza-skills-fixes-2026-03-09 \
  --path scientific-skills/research-grants scientific-skills/peer-review scientific-skills/hypothesis-generation \
         scientific-skills/scientific-schematics scientific-skills/scientific-critical-thinking scientific-skills/scholar-evaluation \
         scientific-skills/scientific-brainstorming scientific-skills/literature-review scientific-skills/citation-management \
         scientific-skills/research-lookup
```

## Update cycle when upstream changes

1. Sync `main` with upstream:
```bash
git checkout main
git fetch upstream
git merge --ff-only upstream/main
git push origin main
```

2. Rebase your fixes branch on updated `main`:
```bash
git checkout codex/fixes-skill-hardening-2026-03-09
git rebase main
```

3. Run regression tests:
```bash
python3 scientific-skills/scholar-evaluation/scripts/test_calculate_scores.py
python3 scientific-skills/scientific-schematics/scripts/test_generate_schematic_ai.py
python3 scientific-skills/citation-management/scripts/test_validate_citations.py
```

4. If tests pass, push branch and cut a new tag:
```bash
git push --force-with-lease origin codex/fixes-skill-hardening-2026-03-09
git tag -a mazza-skills-fixes-YYYY-MM-DD -m "Pinned skill fixes snapshot YYYY-MM-DD"
git push origin mazza-skills-fixes-YYYY-MM-DD
```

## Optional upstream contribution

Open PRs from your branch to `K-Dense-AI/claude-scientific-skills` for fixes that should be upstreamed.

