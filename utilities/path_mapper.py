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
from typing import Optional, Tuple
from utilities.debug_utils import debug


class PathMapper:
    """
    Manages path conversion between absolute and relative paths,
    handling cross-platform network drive mounting differences.
    """
    
    def __init__(self, network_root: str):
        """
        Initialize the path mapper with a network root path.
        
        Args:
            network_root: Absolute path to the network drive root
                         e.g., "/Volumes/Marketing" or "Z:\\"
        """
        self.network_root = Path(network_root).resolve()
        self.os_type = platform.system()  # 'Darwin', 'Windows', 'Linux'
        
        debug("paths", f"PathMapper initialized: root={self.network_root}, os={self.os_type}")
        
        # Validate that network root exists
        if not self.network_root.exists():
            debug("errors", f"WARNING: Network root does not exist: {self.network_root}")
    
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
        try:
            abs_path = Path(absolute_path).resolve()
            
            # Check if path is under network root
            try:
                relative = abs_path.relative_to(self.network_root)
                # Use forward slashes for cross-platform compatibility in CSV
                rel_str = str(relative).replace(os.sep, '/')
                debug("paths", f"to_relative: {absolute_path} -> {rel_str}")
                return rel_str
            except ValueError:
                # Path is not relative to network root
                debug("errors", f"Path not under network root: {absolute_path}")
                return None
                
        except Exception as e:
            debug("errors", f"Error converting to relative path: {e}")
            return None
    
    def to_absolute(self, relative_path: str) -> str:
        """
        Convert relative path to absolute path using network root.
        
        Args:
            relative_path: Path relative to network root (forward slashes)
            
        Returns:
            Absolute path as string
            
        Example:
            relative: "Photos/2026/IMG_001.jpg"
            absolute: "/Volumes/Marketing/Photos/2026/IMG_001.jpg"
        """
        try:
            # Convert forward slashes to OS-specific separators
            rel_path = relative_path.replace('/', os.sep)
            absolute = self.network_root / rel_path
            abs_str = str(absolute)
            debug("paths", f"to_absolute: {relative_path} -> {abs_str}")
            return abs_str
            
        except Exception as e:
            debug("errors", f"Error converting to absolute path: {e}")
            # Return constructed path even if error
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
        return f"PathMapper(root={self.network_root}, os={self.os_type})"
    
    def __repr__(self) -> str:
        return self.__str__()
