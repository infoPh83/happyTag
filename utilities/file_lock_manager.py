"""
File Lock Manager - Single-user access control for shared resources

Implements file-based locking mechanism to ensure only one user can
access the folder management system at a time. Includes timeout and
inactivity detection.

Author: HappyTag Development Team
Date: May 2026
"""

import os
import time
import platform
import getpass
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from utilities.debug_utils import debug


class LockError(Exception):
    """Raised when unable to acquire or release lock"""
    pass


class FileLockManager:
    """
    Manages file-based locking for single-user access control.
    
    Lock file contains:
    - username
    - hostname
    - timestamp
    - process_id
    """
    
    LOCK_FILENAME = ".happytag_folder.lock"
    TIMEOUT_MINUTES = 10
    
    def __init__(self, lock_directory: str):
        """
        Initialize the lock manager.
        
        Args:
            lock_directory: Directory where lock file will be created
                           (typically the network drive root)
        """
        self.lock_directory = Path(lock_directory)
        self.lock_file = self.lock_directory / self.LOCK_FILENAME
        self.username = getpass.getuser()
        self.hostname = platform.node()
        self.process_id = os.getpid()
        self.last_activity = time.time()
        
        debug("locking", f"FileLockManager initialized: {self.lock_file}")
        debug("locking", f"User: {self.username}@{self.hostname}, PID: {self.process_id}")
    
    def acquire_lock(self, force: bool = False) -> Tuple[bool, str]:
        """
        Attempt to acquire the lock.
        
        Args:
            force: If True, override existing lock (use with caution)
            
        Returns:
            Tuple of (success, message)
        """
        debug("locking", f"Attempting to acquire lock (force={force})")
        
        # Check if lock file exists
        if self.lock_file.exists():
            # Read existing lock
            existing_lock = self._read_lock()
            
            if existing_lock:
                # Check if lock is expired
                if self._is_lock_expired(existing_lock):
                    debug("locking", f"Existing lock expired, removing: {existing_lock}")
                    self._remove_lock_file()
                elif (existing_lock.get('username') == self.username and
                      existing_lock.get('hostname') == self.hostname and
                      existing_lock.get('process_id') == self.process_id):
                    # Same process re-acquiring its own lock — allow it
                    debug("locking", "Re-acquiring own lock (same process)")
                    self._remove_lock_file()
                elif not force:
                    # Lock is valid and held by another user or another instance
                    lock_age = self._get_lock_age(existing_lock)
                    holder = f"{existing_lock['username']}@{existing_lock['hostname']}"
                    if existing_lock.get('process_id') and existing_lock.get('hostname') == self.hostname:
                        holder += f" (another instance on this machine)"
                    msg = (f"Folder Manager is already open by {holder}\n"
                           f"Lock acquired {lock_age} minutes ago\n"
                           f"Lock will expire in {self.TIMEOUT_MINUTES - lock_age} minutes")
                    debug("locking", f"Lock acquisition failed: {msg}")
                    return False, msg
                else:
                    debug("locking", "Force flag set, overriding existing lock")
                    self._remove_lock_file()
        
        # Create lock file
        try:
            lock_data = {
                'username': self.username,
                'hostname': self.hostname,
                'process_id': self.process_id,
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'timeout_minutes': self.TIMEOUT_MINUTES
            }
            
            with open(self.lock_file, 'w') as f:
                json.dump(lock_data, f, indent=2)
            
            self.last_activity = time.time()
            debug("locking", f"Lock acquired successfully: {lock_data}")
            return True, f"Lock acquired by {self.username}@{self.hostname}"
            
        except Exception as e:
            msg = f"Failed to create lock file: {e}"
            debug("errors", msg)
            return False, msg
    
    def release_lock(self) -> Tuple[bool, str]:
        """
        Release the lock if held by current user.
        
        Returns:
            Tuple of (success, message)
        """
        debug("locking", "Attempting to release lock")
        
        if not self.lock_file.exists():
            debug("locking", "No lock file found")
            return True, "No lock to release"
        
        # Verify lock is held by current user
        existing_lock = self._read_lock()
        if not existing_lock:
            debug("errors", "Failed to read lock file")
            return False, "Failed to read lock file"
        
        if (existing_lock['username'] != self.username or 
            existing_lock['hostname'] != self.hostname or
            existing_lock.get('process_id') != self.process_id):
            msg = f"Lock is held by {existing_lock['username']}@{existing_lock['hostname']} (PID {existing_lock.get('process_id', '?')})"
            debug("errors", f"Cannot release lock: {msg}")
            return False, msg
        
        # Remove lock file
        return self._remove_lock_file()
    
    def refresh_lock(self) -> bool:
        """
        Refresh the lock timestamp to prevent timeout.
        Should be called periodically during active use.
        
        Returns:
            True if lock was refreshed, False otherwise
        """
        if not self.lock_file.exists():
            debug("errors", "Cannot refresh: lock file does not exist")
            return False
        
        # Verify lock is held by current user
        existing_lock = self._read_lock()
        if not existing_lock:
            return False
        
        if (existing_lock['username'] != self.username or 
            existing_lock['hostname'] != self.hostname or
            existing_lock.get('process_id') != self.process_id):
            debug("errors", "Cannot refresh: lock held by another user/process")
            return False
        
        # Update timestamp
        try:
            existing_lock['timestamp'] = time.time()
            existing_lock['datetime'] = datetime.now().isoformat()
            
            with open(self.lock_file, 'w') as f:
                json.dump(existing_lock, f, indent=2)
            
            self.last_activity = time.time()
            debug("locking", "Lock refreshed successfully")
            return True
            
        except Exception as e:
            debug("errors", f"Failed to refresh lock: {e}")
            return False
    
    def check_inactivity(self) -> Tuple[bool, float]:
        """
        Check if user has been inactive beyond timeout threshold.
        
        Returns:
            Tuple of (is_inactive, minutes_inactive)
        """
        inactive_time = (time.time() - self.last_activity) / 60  # minutes
        is_inactive = inactive_time >= self.TIMEOUT_MINUTES
        
        if is_inactive:
            debug("locking", f"User inactive for {inactive_time:.1f} minutes")
        
        return is_inactive, inactive_time
    
    def update_activity(self):
        """
        Update the last activity timestamp.
        Call this whenever user performs an action.
        """
        self.last_activity = time.time()
        debug("locking", "Activity timestamp updated")
    
    def get_lock_info(self) -> Optional[Dict]:
        """
        Get information about the current lock.
        
        Returns:
            Lock data dictionary, or None if no lock exists
        """
        if not self.lock_file.exists():
            return None
        
        return self._read_lock()
    
    def is_locked_by_me(self) -> bool:
        """
        Check if lock is held by current user/process.
        
        Returns:
            True if lock is held by current user, False otherwise
        """
        lock_info = self.get_lock_info()
        if not lock_info:
            return False
        
        is_mine = (lock_info['username'] == self.username and 
                   lock_info['hostname'] == self.hostname and
                   lock_info.get('process_id') == self.process_id)
        
        debug("locking", f"is_locked_by_me: {is_mine}")
        return is_mine
    
    def _read_lock(self) -> Optional[Dict]:
        """
        Read lock file contents.
        
        Returns:
            Lock data dictionary, or None if error
        """
        try:
            with open(self.lock_file, 'r') as f:
                lock_data = json.load(f)
            debug("locking", f"Lock file read: {lock_data}")
            return lock_data
        except Exception as e:
            debug("errors", f"Failed to read lock file: {e}")
            return None
    
    def _remove_lock_file(self) -> Tuple[bool, str]:
        """
        Remove the lock file.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            self.lock_file.unlink()
            debug("locking", "Lock file removed successfully")
            return True, "Lock released"
        except Exception as e:
            msg = f"Failed to remove lock file: {e}"
            debug("errors", msg)
            return False, msg
    
    def _is_lock_expired(self, lock_data: Dict) -> bool:
        """
        Check if a lock has expired based on timeout.
        
        Args:
            lock_data: Lock data dictionary
            
        Returns:
            True if lock is expired, False otherwise
        """
        lock_age = (time.time() - lock_data['timestamp']) / 60  # minutes
        is_expired = lock_age >= self.TIMEOUT_MINUTES
        
        debug("locking", f"Lock age: {lock_age:.1f} minutes, expired: {is_expired}")
        return is_expired
    
    def _get_lock_age(self, lock_data: Dict) -> int:
        """
        Get the age of a lock in minutes.
        
        Args:
            lock_data: Lock data dictionary
            
        Returns:
            Lock age in minutes
        """
        age = int((time.time() - lock_data['timestamp']) / 60)
        return age
    
    def __enter__(self):
        """Context manager entry: acquire lock"""
        success, msg = self.acquire_lock()
        if not success:
            raise LockError(msg)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: release lock"""
        self.release_lock()
        return False
    
    def __str__(self) -> str:
        lock_info = self.get_lock_info()
        if lock_info:
            return f"FileLockManager(locked by {lock_info['username']}@{lock_info['hostname']})"
        return f"FileLockManager(unlocked)"
    
    def __repr__(self) -> str:
        return self.__str__()
