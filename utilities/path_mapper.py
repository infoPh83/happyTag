"""
Path Mapper - Cross-platform path handling for network drives

Handles conversion between absolute and relative paths, supports different
mount points across operating systems, and detects missing/moved folders.

Author: HappyTag Development Team
Date: May 2026
"""

import os
import platform
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from utilities.debug_utils import debug


class PathMapper:
    """
    Manages path conversion between absolute and relative paths,
    handling cross-platform network drive mounting differences.

    Supports multiple named roots (e.g. an Azure network drive and a
    per-user OneDrive/SharePoint sync folder). Each root maps to a local
    absolute prefix; relative paths within each root are shared and
    consistent across machines.
    """

    def __init__(self, network_root: str, extra_roots: Optional[List[Dict[str, str]]] = None,
                 root_codes: Optional[List[str]] = None, primary_name: Optional[str] = None):
        """
        Initialize the path mapper with one or more root paths.

        Args:
            network_root: Absolute path to the primary network drive root
                          e.g., "/Volumes/Marketing" or "G:\\Marketing"
            extra_roots: Optional list of additional roots, each a dict with
                         'code', 'name' and 'path' keys. The primary root is
                         assigned code 'A' unless root_codes says otherwise.
            root_codes: Optional list parallel to [primary] + extra_roots giving
                        each root a stable code (e.g. 'A', 'B'). When omitted,
                        codes are assigned positionally ('A', 'B', ...).
        """
        # Build the root list: primary first, then extras.
        # NOTE: we normalise but do NOT call .resolve() — on Windows a mapped
        # drive letter (G:) resolves to its UNC target, which would then fail
        # to match paths the user browses to via the drive letter (and vice
        # versa). We keep the exact form the user configured.
        raw_roots = [(primary_name or self._root_label(Path(network_root)), network_root)]
        if extra_roots:
            raw_roots.extend((r.get('name', ''), r.get('path', '')) for r in extra_roots)

        codes = root_codes or [chr(ord('A') + i) for i in range(len(raw_roots))]

        # _roots: list of (code, name, Path), primary first.
        self._roots: List[Tuple[str, str, Path]] = []
        seen = []
        for (name, path_str), code in zip(raw_roots, codes):
            try:
                p = self._normalize_root(path_str)
                if any(self._same_path(p, e) for e in seen):
                    continue
                seen.append(p)
                label = name or self._root_label(p)
                self._roots.append((code, label, p))
            except Exception as e:
                debug("errors", f"Skipping invalid root {path_str}: {e}")

        # Backward-compatible primary root attribute (the explicitly-passed root).
        self.network_root = self._roots[0][2]
        self.primary_code = self._roots[0][0]
        self.os_type = platform.system()  # 'Darwin', 'Windows', 'Linux'

        # Sort a separate matching list longest-path-first so nested roots
        # resolve correctly. self._roots keeps primary-first ordering.
        self._match_order = sorted(self._roots, key=lambda item: len(str(item[2])), reverse=True)

        debug("paths", f"PathMapper initialized: roots={[(c, str(p)) for c, _, p in self._roots]}, os={self.os_type}")

        # Validate roots exist
        for code, name, root in self._roots:
            if not root.exists():
                debug("errors", f"WARNING: Root '{name}' does not exist: {root}")

    @staticmethod
    def _normalize_root(path_str: str) -> Path:
        """
        Normalise a configured root path without resolving mapped-drive
        letters to their UNC targets. Absolute-ifies and collapses redundant
        separators / trailing slashes, preserving the user's chosen form.
        """
        p = Path(str(path_str).strip())
        # os.path.abspath normalises without resolving symlinks/mapped drives.
        return Path(os.path.abspath(str(p)))

    @staticmethod
    def _same_path(a: Path, b: Path) -> bool:
        """Case-insensitive path equality (Windows-safe)."""
        return os.path.normcase(str(a)) == os.path.normcase(str(b))

    @staticmethod
    def _root_label(path: Path) -> str:
        """Derive a display label for a root (drive letter or folder name)."""
        drive = path.drive
        if drive:
            return drive.rstrip(':').rstrip(os.sep).upper() or str(path)
        return path.name or str(path)

    @property
    def roots(self) -> List[Tuple[str, str, Path]]:
        """All configured roots as (code, name, absolute Path) tuples, primary first."""
        return list(self._roots)

    def root_names(self) -> List[str]:
        """Display names of all configured roots."""
        return [name for _, name, _ in self._roots]

    def root_codes(self) -> List[str]:
        """Stable codes of all configured roots."""
        return [code for code, _, _ in self._roots]

    def root_label(self, code: str) -> str:
        """Display label for a root code, or the code itself if unknown."""
        for c, name, _ in self._roots:
            if c == code:
                return name
        return code

    def path_for_code(self, code: str) -> Optional[Path]:
        """Absolute Path for a root code, or None."""
        for c, _, p in self._roots:
            if c == code:
                return p
        return None

    def _normalize_input(self, absolute_path: str) -> Optional[Path]:
        """Normalise an input absolute path (no mapped-drive -> UNC resolution)."""
        try:
            return Path(os.path.abspath(str(absolute_path).strip()))
        except Exception:
            return None

    def _matching_root(self, absolute_path: str) -> Optional[Tuple[str, str, Path]]:
        """Return the (code, name, root) that contains absolute_path, or None."""
        abs_path = self._normalize_input(absolute_path)
        if abs_path is None:
            return None
        for code, name, root in self._match_order:
            # Case-insensitive containment for Windows drive paths.
            if self._is_under(abs_path, root):
                return (code, name, root)
        return None

    @staticmethod
    def _is_under(path: Path, root: Path) -> bool:
        """True if path is root or inside root, compared case-insensitively."""
        p = os.path.normcase(str(path))
        r = os.path.normcase(str(root))
        if p == r:
            return True
        # Ensure we compare on a path-boundary basis.
        return p.startswith(r if r.endswith(os.sep) else r + os.sep)

    def to_relative(self, absolute_path: str) -> Optional[str]:
        """
        Convert absolute path to relative path from network root.
        
        Args:
            absolute_path: Full path to file or folder
            
        Returns:
            Relative path as string, or None if path is not under network root
            
        Example:
            absolute: "/Volumes/Marketing/Photos/2026/IMG_001.jpg"
            relative: "Photos/2026/IMG_001.jpg"
        """
        abs_path = self._normalize_input(absolute_path)
        if abs_path is None:
            debug("errors", f"Error converting to relative path: unusable path {absolute_path}")
            return None

        try:
            # Check if path is under any configured root (longest first)
            for code, name, root in self._match_order:
                if not self._is_under(abs_path, root):
                    continue
                # Compute the relative portion against this root.
                rel = os.path.relpath(str(abs_path), str(root))
                # os.path.relpath returns '.' when they're identical.
                if rel == '.':
                    rel_str = ''
                else:
                    rel_str = rel.replace(os.sep, '/')
                debug("paths", f"to_relative: {absolute_path} -> {rel_str} (root={name})")
                return rel_str

            # Path is not relative to any root
            debug("errors", f"Path not under any configured root: {absolute_path}")
            return None

        except Exception as e:
            debug("errors", f"Error converting to relative path: {e}")
            return None

    def to_qualified(self, absolute_path: str) -> Optional[Tuple[str, str]]:
        """
        Convert an absolute path to (root_code, relative_path).

        Returns None if the path is under no configured root. The relative
        path uses forward slashes and is empty string when the path IS a root.
        """
        abs_path = self._normalize_input(absolute_path)
        if abs_path is None:
            return None
        for code, name, root in self._match_order:
            if not self._is_under(abs_path, root):
                continue
            rel = os.path.relpath(str(abs_path), str(root))
            rel_str = '' if rel == '.' else rel.replace(os.sep, '/')
            debug("paths", f"to_qualified: {absolute_path} -> ({code}, {rel_str})")
            return (code, rel_str)
        debug("errors", f"Path not under any configured root: {absolute_path}")
        return None

    def to_absolute_qualified(self, root_code: str, relative_path: str) -> str:
        """
        Convert (root_code, relative_path) to an absolute path on this machine.
        Falls back to primary root if the code is unknown.
        """
        root = self.path_for_code(root_code) or self.network_root
        rel_path = (relative_path or '').replace('/', os.sep)
        return str(root / rel_path) if rel_path else str(root)

    def to_absolute(self, relative_path: str) -> str:
        """
        Convert relative path to absolute path.

        With a single root this simply joins the root and the relative path.
        With multiple roots, it resolves against the root under which the
        relative path actually exists on disk (primary root first, then each
        extra root). If it exists under none, it falls back to the primary
        root so callers still get a well-formed absolute path.

        Args:
            relative_path: Path relative to a root (forward slashes)

        Returns:
            Absolute path as string
        """
        try:
            rel_path = relative_path.replace('/', os.sep)

            # Fast path: single root (or path exists under primary root).
            primary_candidate = self.network_root / rel_path
            if len(self._roots) == 1 or primary_candidate.exists():
                debug("paths", f"to_absolute: {relative_path} -> {primary_candidate}")
                return str(primary_candidate)

            # Multi-root: find which root actually contains this relative path.
            # Skip the primary (already checked above); check the rest.
            for code, name, root in self._match_order:
                if root == self.network_root:
                    continue
                candidate = root / rel_path
                if candidate.exists():
                    debug("paths", f"to_absolute: {relative_path} -> {candidate} (root={name})")
                    return str(candidate)

            # Not found anywhere; fall back to primary for a well-formed path.
            debug("paths", f"to_absolute (fallback): {relative_path} -> {primary_candidate}")
            return str(primary_candidate)

        except Exception as e:
            debug("errors", f"Error converting to absolute path: {e}")
            return str(self.network_root / relative_path.replace('/', os.sep))
    
    def exists(self, relative_path: str) -> bool:
        """
        Check if a relative path exists on the file system.
        
        Args:
            relative_path: Path relative to network root
            
        Returns:
            True if path exists, False otherwise
        """
        absolute = self.to_absolute(relative_path)
        exists = Path(absolute).exists()
        debug("paths", f"exists check: {relative_path} -> {exists}")
        return exists
    
    def is_directory(self, relative_path: str) -> bool:
        """
        Check if a relative path is a directory.
        
        Args:
            relative_path: Path relative to network root
            
        Returns:
            True if path exists and is a directory, False otherwise
        """
        absolute = self.to_absolute(relative_path)
        is_dir = Path(absolute).is_dir()
        debug("paths", f"is_directory check: {relative_path} -> {is_dir}")
        return is_dir
    
    def is_file(self, relative_path: str) -> bool:
        """
        Check if a relative path is a file.
        
        Args:
            relative_path: Path relative to network root
            
        Returns:
            True if path exists and is a file, False otherwise
        """
        absolute = self.to_absolute(relative_path)
        is_file = Path(absolute).is_file()
        debug("paths", f"is_file check: {relative_path} -> {is_file}")
        return is_file
    
    def get_parent(self, relative_path: str) -> Optional[str]:
        """
        Get the parent folder of a relative path.
        
        Args:
            relative_path: Path relative to network root
            
        Returns:
            Parent path as string, or None if at root level
        """
        if not relative_path or relative_path == '.':
            return None
            
        parent = str(Path(relative_path).parent)
        if parent == '.':
            return None
            
        # Use forward slashes for consistency
        parent = parent.replace(os.sep, '/')
        debug("paths", f"get_parent: {relative_path} -> {parent}")
        return parent
    
    def join(self, *parts: str) -> str:
        """
        Join path parts into a relative path with forward slashes.
        
        Args:
            *parts: Path components to join
            
        Returns:
            Joined path with forward slashes
        """
        joined = '/'.join(parts)
        debug("paths", f"join: {parts} -> {joined}")
        return joined
    
    def get_name(self, relative_path: str) -> str:
        """
        Get the name (last component) of a path.
        
        Args:
            relative_path: Path relative to network root
            
        Returns:
            Name of file or folder
        """
        name = Path(relative_path).name
        debug("paths", f"get_name: {relative_path} -> {name}")
        return name
    
    def validate_network_root(self) -> Tuple[bool, str]:
        """
        Validate that the network root is accessible.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.network_root.exists():
            msg = f"Network root not found: {self.network_root}"
            debug("errors", msg)
            return False, msg
        
        if not self.network_root.is_dir():
            msg = f"Network root is not a directory: {self.network_root}"
            debug("errors", msg)
            return False, msg
        
        # Try to list contents to verify access
        try:
            list(self.network_root.iterdir())
            debug("paths", f"Network root validated successfully: {self.network_root}")
            return True, ""
        except PermissionError:
            msg = f"No permission to access network root: {self.network_root}"
            debug("errors", msg)
            return False, msg
        except Exception as e:
            msg = f"Error accessing network root: {e}"
            debug("errors", msg)
            return False, msg
    
    def find_common_root(self, path1: str, path2: str) -> Optional[str]:
        """
        Find common root between two relative paths.
        
        Args:
            path1: First relative path
            path2: Second relative path
            
        Returns:
            Common root path, or None if no common root
        """
        parts1 = path1.split('/')
        parts2 = path2.split('/')
        
        common = []
        for p1, p2 in zip(parts1, parts2):
            if p1 == p2:
                common.append(p1)
            else:
                break
        
        if common:
            result = '/'.join(common)
            debug("paths", f"find_common_root: {path1} & {path2} -> {result}")
            return result
        
        return None
    
    def normalize_path(self, path: str) -> str:
        """
        Normalize a path to use forward slashes and remove redundant separators.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        # Replace backslashes with forward slashes
        normalized = path.replace('\\', '/')
        
        # Remove duplicate slashes
        while '//' in normalized:
            normalized = normalized.replace('//', '/')
        
        # Remove trailing slash
        normalized = normalized.rstrip('/')
        
        debug("paths", f"normalize_path: {path} -> {normalized}")
        return normalized
    
    def __str__(self) -> str:
        roots_str = ", ".join(f"{c}({n}):{p}" for c, n, p in self._roots)
        return f"PathMapper(roots=[{roots_str}], os={self.os_type})"

    def __repr__(self) -> str:
        return self.__str__()


def create_path_mapper(network_root: Optional[str] = None) -> 'PathMapper':
    """
    Build a PathMapper covering all configured shared roots, each tagged with
    its stable code ('A' = Marketing Drive, 'B' = Share Point Media Library).

    Reads the shared-root slots from settings. The primary root is the
    Marketing Drive (code 'A'); the SharePoint root (code 'B') is added when
    configured.

    Args:
        network_root: Kept for backward compatibility; when given it must be
                      the primary (Marketing Drive) root. Defaults to the
                      configured Marketing Drive path.

    Returns:
        A PathMapper configured with every configured shared root.
    """
    from utilities.settings_dialog import SettingsDialog
    roots = SettingsDialog.get_shared_roots()  # [{'code','name','path'}, ...]

    if not roots:
        # Nothing configured: fall back to whatever primary was passed in.
        primary = network_root or SettingsDialog.get_network_root()
        return PathMapper(primary)

    # Primary is the first configured root (Marketing Drive / code A).
    primary_root = network_root or roots[0]['path']
    primary_code = roots[0]['code']
    primary_name = roots[0]['name']

    extras = []
    extra_codes = []
    primary_norm = os.path.normcase(os.path.abspath(str(primary_root)))
    for r in roots[1:]:
        if not r.get('path'):
            continue
        # Skip if it duplicates the primary.
        if os.path.normcase(os.path.abspath(r['path'])) == primary_norm:
            continue
        extras.append({'name': r['name'], 'path': r['path']})
        extra_codes.append(r['code'])

    return PathMapper(primary_root, extra_roots=extras,
                      root_codes=[primary_code] + extra_codes,
                      primary_name=primary_name)
