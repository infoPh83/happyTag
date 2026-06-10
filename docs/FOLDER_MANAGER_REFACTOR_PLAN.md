# Folder Manager Refactor Plan
*Created: 2026-06-10*

---

## Background

The folder status manager was originally a full-filesystem scanner that ran on every folder expansion. That proved too expensive on shared/network drives. It was replaced with an explicit-scan model, but the migration left the codebase incoherent in several ways documented below. This plan describes the intended post-refactor state.

---

## Core Concept (unchanged)

The user watches certain folders on a shared filesystem to track how many images:
- exist in total (direct + nested)
- have been uploaded to Cloudinary (`on_cloud`)
- have been dismissed (`dismissed`)
- are still pending (`new`)

Folders are never auto-watched. The user explicitly marks folders as **Watched** or **Dismissed**.

---

## Status Model (post-refactor)

### Folder statuses (stored in CSV)

| Status | Meaning | How assigned |
|---|---|---|
| `dismissed` | Not being monitored | Default for all folders; set by user |
| `watched` | Actively monitored | Set by user (always recursive) |
| `part_watched` | Contains at least one watched descendant | Auto-computed; stored in CSV |
| `not_found` | Was tracked but path no longer exists on FS | Set during Refresh scan |

### Folder statuses (ephemeral, UI-only, NOT stored in CSV)

| Status | Meaning | When it appears |
|---|---|---|
| `new` | Folder exists on FS but was not in CSV | Root scan at dialog open (shallow); or when a Refresh reveals a new sub-folder |

The `new` visual label is shown **only for the current session**. The folder is stored in the CSV as `dismissed`. On next launch it simply appears as dismissed.

### File statuses (stored in CSV)

| Status | Meaning |
|---|---|
| `new` | Discovered in a watched folder, not yet processed |
| `on_cloud` | Uploaded to Cloudinary |
| `dismissed` | Skipped by user |
| `not_found` | Was tracked but file no longer exists on FS |

---

## Actions / UI

### Top toolbar

| Control | Behaviour |
|---|---|
| **Refresh** button | **Enabled only when a `watched` or `part_watched` folder is selected.** Disabled (greyed out) when nothing is selected or a `dismissed` / `not_found` folder is selected. Runs `reconcile_folder_with_filesystem()` on the selected folder: full `os.walk`, discovers new sub-folders and files, marks missing items as `not_found`, updates all counters (Direct, Nested, On Cloud, Dismissed, New). This replaces the old "Refresh" (CSV-only reload) AND the two right-click scan actions. |
| Search box | Filter by folder name (unchanged) |
| Status filter | Filter by status (unchanged) |
| Expand All / Collapse All | Unchanged |
| Reset DB | Unchanged (danger button) |

> **Removed:** The old "Refresh" button that only reloaded from CSV without touching the filesystem.  
> **Note:** There is no "refresh all" / batch reconcile operation. The user must select a specific watched folder and press Refresh. This is intentional to avoid expensive uncontrolled scans on shared drives.

### Tree behaviour on open

1. Load CSV into memory.
2. Do a **shallow `iterdir()` of the network root** only — match names against CSV.
   - Folders in both: show with their CSV status.
   - Folders on FS but not in CSV: add to CSV as `dismissed`; show with ephemeral `new` badge in the UI.
   - Folders in CSV but not on FS: show as `not_found`.
3. This is the only automatic filesystem I/O on open. No recursive seeding.

> **Removed:** First-launch `seed_folder_structure()` full recursive walk.

### Right-click context menu

#### On any folder:
- **Set Watched** — mark this folder and all descendants as `watched`; trigger `reconcile_folder_with_filesystem()` immediately
- **Set Dismissed** — mark this folder and all descendants as `dismissed`; purge descendant entries from CSV

#### On `not_found` folders only:
- **Relocate…** — see Relocation Workflow below
- **Dismiss** *(replaces "Acknowledge (Remove from DB)")* — removes this folder and all its descendants from the CSV; the user accepts the data loss

#### On `watched` / `part_watched` folders:
- **Refresh** *(same as toolbar Refresh but scoped to this folder)* — explicit filesystem reconcile

---

## Relocation Workflow (new feature)

When the user picks "Relocate…" on a `not_found` folder:

### Step 1 — Pick new location
Show a native folder-picker dialog. The user selects the folder's new path on the filesystem.

### Step 2 — Structural verification
Before writing anything to the CSV:
1. Recursively scan **folder names only** (no file stat calls) of the candidate path.
2. Compare the folder tree against what the CSV recorded under the old path.
3. Build a discrepancy report:
   - Sub-folders that exist in the CSV but are **missing** from the new location.
   - Sub-folders that exist in the new location but are **not in the CSV** (new additions).

### Step 3 — Confirmation dialog
Show a summary dialog with:
- The old path → new path mapping
- Count of sub-folders matched
- List of discrepancies (missing / extra folders), paginated if long
- Two buttons: **Confirm Relocation** / **Cancel**

If discrepancies exist, a warning is shown but the user is still allowed to confirm (they may have intentionally reorganised the sub-folder structure).

### Step 4 — CSV update
On confirmation:
1. Walk all entries in the CSV whose path starts with the old relative path.
2. Rewrite each entry with the new relative path prefix (cascade rename).
3. Save CSV.
4. Reload the affected tree nodes.

Implementation: extend `remap_path()` in `FolderStatusManager` to handle cascade renames (currently it only moves a single entry).

---

## Code Changes Required

### `folder_status_manager.py`
- [ ] Extend `remap_path()` to cascade-rename all child paths
- [ ] Remove / deprecate `seed_folder_structure()` (replaced by shallow root scan)
- [ ] Remove `STATUS_NEW` from `ALL_STATUSES` (it stays as a constant but is never written to CSV for folders)
- [ ] Remove the migration guard `status == STATUS_NEW and item_type == 'folder'` (can stay as a safety net initially)
- [ ] Add `compare_folder_structure(old_rel_path, new_abs_path) -> dict` for relocation verification

### `folder_status_dialog.py`
- [ ] Remove old "Refresh" button handler (`_refresh_tree` — the CSV-only reload)
- [ ] Add new "Refresh" button that calls `reconcile_folder_with_filesystem()` (scoped or global)
- [ ] Remove `_rescan_folder_structure()` (replaced by new Refresh)
- [ ] Remove `_deep_scan_folder()` and its dependency on legacy `FolderScanner`
- [ ] Replace right-click "Re-scan Folder Structure" and "Deep Scan (Recursive)" with single "Refresh" action
- [ ] Replace right-click "Acknowledge (Remove from DB)" with "Dismiss"
- [ ] Add right-click "Relocate…" for `not_found` folders
- [ ] Implement `_relocate_folder()` — folder picker → structural comparison → confirm dialog → cascade remap
- [ ] Change `_collect_root_items()` to: assign `dismissed` to new root folders in CSV, but pass an `is_new_this_session` flag for UI badge display (instead of setting `STATUS_NEW` in the CSV)
- [ ] Remove `_run_first_launch_seed()` call from `_load_root_folders()`

### `folder_scanner.py`
- [ ] Assess whether `FolderScanner` class is still needed after removing `_deep_scan_folder()`
- [ ] If `FolderScanner` becomes dead code after the refactor, delete the file

---

## Things to Keep As-Is

- Background worker pattern (QThread) for all filesystem I/O
- `count_from_cache()` for cheap UI updates after dismiss/upload (no FS walk)
- `propagate_status_to_ancestors()` and `recompute_all_inferred_statuses()`
- `part_watched` stored in CSV (computed once, stored, recomputed on load)
- File lock manager for multi-instance safety
- `update_file_status()` / `batch_update_file_statuses()` called from main window on dismiss/upload
- `purge_from_db()` (used by new "Dismiss" on not_found folders)

---

## Open Questions / Decisions Made

| Topic | Decision |
|---|---|
| Watch scope | Always recursive — "watch a folder" means watch all sub-folders |
| `new` folder status | Ephemeral UI badge only; stored as `dismissed` in CSV |
| Refresh scope | Toolbar Refresh = scoped to selected watched/part-watched folder only; disabled when nothing (or a dismissed/not_found folder) is selected. No global "refresh all" operation. |
| Relocation safety | Structural folder scan + discrepancy report before any CSV write |
| First-launch performance | No full tree seed; shallow root scan only |
| `FolderScanner` class | Retire after `_deep_scan_folder()` is removed |

---

*End of plan*
