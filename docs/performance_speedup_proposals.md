# Folder Status Dialog — Performance Speedup Proposals

Recorded 29 May 2026. Pick up in a future session.

---

## Context

Opening the Folder Status Dialog is slow because it must reconcile watched/part-watched root
folders against the SMB network filesystem at startup. Each reconciliation calls
`folder_path.rglob('*')`, which issues a stat call per filesystem entry across the network.
Sorting the CSV would have no effect — once loaded, all lookups are O(1) dict operations.

---

## Proposal 1 — Quick win: fix `_inside_dismissed_folder` (low effort, immediate gain)

**File:** `utilities/folder_status_manager.py` — `_reconcile_watched_folder`

**Problem:** The helper added on 29 May 2026 calls `path_mapper.to_relative()` for every
ancestor of every file during the rglob walk. On a deep tree with thousands of files this
multiplies the lookup cost significantly.

**Fix:** Pre-build a set of *absolute* dismissed folder path strings before the loop, then
replace the ancestor walk with a single `startswith` check:

```python
dismissed_folder_abs = {
    self.path_mapper.to_absolute(p)
    for p in dismissed_folder_rels
}

def _inside_dismissed_folder(item_path: Path) -> bool:
    s = str(item_path) + "/"
    return any(s.startswith(d + "/") for d in dismissed_folder_abs)
```

Because the set is built once, per-item cost drops from O(depth × to_relative) to O(n_dismissed)
— typically a very small number.

---

## Proposal 2 — Background thread reconciliation (medium effort, biggest perceived gain)

**Files:** `utilities/folder_status_dialog.py`, possibly a new `ReconcileWorker` QThread

**Problem:** The dialog blocks the UI while all root folders are reconciled sequentially at
startup.

**Fix:** Show the dialog immediately with cached/blank counts, then run each
`reconcile_folder_with_filesystem` call in a `QThread` worker. Emit a signal per completed
folder; the UI slot calls `_update_tree_item_status` + `_refresh_ancestor_tree_items` on
arrival. The user sees the dialog open instantly and counts populate progressively.

Key points:
- The cache dict must be protected by a `threading.Lock` during concurrent writes.
- A loading spinner or "Calculating…" placeholder in count cells would give good UX feedback.
- The worker should be cancellable (e.g. when the dialog is closed before it finishes).

---

## Proposal 3 — Defer root-level reconciliation to expand (medium effort)

**File:** `utilities/folder_status_dialog.py` — `_populate_root_items` / `__init__`

**Problem:** All root-level watched/part-watched folders are reconciled at dialog open, even
those the user never expands.

**Fix:** At startup, only load root rows with blank count cells (status colour only). When the
user expands a root row for the first time, run `reconcile_folder_with_filesystem` then.
This is already done for second-level folders; extending it to root folders would eliminate
almost all startup I/O for typical usage where only a few folders are opened per session.

Trade-off: first-expand of a root folder would be slow instead of dialog-open. Combine with
Proposal 2 (background thread on expand) to avoid blocking the UI even then.

---

## Priority recommendation

1. **Proposal 1** first — smallest change, no UX impact, measurable speedup.
2. **Proposal 2** second — eliminates the freeze entirely, best user experience.
3. **Proposal 3** optionally, as a further refinement on top of 2.
