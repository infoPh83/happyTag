"""
Centralized session logging manager for HappyTag
Provides unified logging across CloudinaryUpdater, ImageAssessment, and other components
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from utilities.debug_utils import debug_errors, debug_startup


class SessionLogger:
    """
    Centralized session logger that tracks the current active log file
    and provides unified logging across all HappyTag components
    """
    
    _instance: Optional['SessionLogger'] = None
    _current_log_file: Optional[Path] = None
    _log_folder: Optional[Path] = None
    _session_active: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._current_log_file = None
            self._log_folder = None
            self._session_active = False
    
    def configure_log_folder(self, log_folder_path: str) -> bool:
        """
        Configure the log folder path from settings
        
        Args:
            log_folder_path: Path to the log folder from settings
            
        Returns:
            bool: True if successfully configured, False otherwise
        """
        try:
            if not log_folder_path:
                debug_startup("No log folder configured - session logging disabled")
                return False
                
            self._log_folder = Path(log_folder_path)
            self._log_folder.mkdir(parents=True, exist_ok=True)
            debug_startup(f"Session logger configured with folder: {self._log_folder}")
            return True
            
        except Exception as e:
            debug_errors(f"Failed to configure session logger: {e}")
            return False
    
    def start_session(self, session_type: str = "session") -> Optional[Path]:
        """
        Start a new logging session with a timestamped log file
        Uses a single unified log file for all operations in the session
        
        Args:
            session_type: Type of session (kept for backward compatibility, but creates unified file)
            
        Returns:
            Path to the created log file, or None if failed
        """
        try:
            if not self._log_folder:
                debug_startup("Cannot start session - no log folder configured")
                return None
            
            # Return existing log file if session is already active
            if self._session_active and self._current_log_file and self._current_log_file.exists():
                debug_startup(f"Using existing session log file: {self._current_log_file}")
                return self._current_log_file
            
            # Create timestamped unified log file
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_filename = f"happytag_session_{timestamp}.txt"
            self._current_log_file = self._log_folder / log_filename
            
            # Create and initialize log file
            with open(self._current_log_file, 'w', encoding='utf-8') as f:
                session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"=== HappyTag Unified Session Log ===\n")
                f.write(f"Session started: {session_start}\n")
                f.write(f"Log file: {self._current_log_file}\n")
                f.write("=" * 50 + "\n\n")
            
            self._session_active = True
            debug_startup(f"Unified session logging started: {self._current_log_file}")
            return self._current_log_file
            
        except Exception as e:
            debug_errors(f"Failed to start logging session: {e}")
            return None
    
    def get_current_log_file(self) -> Optional[Path]:
        """
        Get the path to the current active log file
        
        Returns:
            Path to current log file, or None if no active session
        """
        if self._session_active and self._current_log_file and self._current_log_file.exists():
            return self._current_log_file
        return None
    
    def get_log_folder(self) -> Optional[Path]:
        """
        Get the configured log folder path
        
        Returns:
            Path to log folder, or None if not configured
        """
        return self._log_folder
    
    def log_message(self, message: str, component: str = "SYSTEM") -> None:
        """
        Log a message to the current log file
        
        Args:
            message: Message to log
            component: Component name (e.g., UPLOAD, ASSESSMENT, etc.)
        """
        if not self._session_active or not self._current_log_file:
            return
            
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            with open(self._current_log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] [{component}] {message}\n")
                f.flush()
        except Exception as e:
            debug_errors(f"Failed to write to log file: {e}")
    
    def get_or_create_session(self) -> Optional[Path]:
        """
        Get current session log file, or create a new session if none exists
        
        Returns:
            Path to the log file, or None if failed
        """
        if self._session_active and self._current_log_file and self._current_log_file.exists():
            return self._current_log_file
        
        # No active session, start a new one
        return self.start_session("session")
    
    def end_session(self) -> None:
        """End the current logging session"""
        if self._session_active and self._current_log_file:
            try:
                with open(self._current_log_file, 'a', encoding='utf-8') as f:
                    session_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"\n{'=' * 50}\n")
                    f.write(f"Session ended: {session_end}\n")
                    f.write("=" * 50 + "\n")
                debug_startup(f"Session logging ended: {self._current_log_file}")
            except Exception as e:
                debug_errors(f"Failed to end logging session: {e}")
        
        self._session_active = False
    
    def is_session_active(self) -> bool:
        """Check if a logging session is currently active"""
        return self._session_active and self._current_log_file is not None


# Convenience functions for easy access
def get_session_logger() -> SessionLogger:
    """Get the singleton SessionLogger instance"""
    return SessionLogger()


def get_current_log_file() -> Optional[Path]:
    """Get the current active log file path"""
    return get_session_logger().get_current_log_file()


def log_session_message(message: str, component: str = "SYSTEM") -> None:
    """
    Log a message to the current session, creating a session if none exists
    
    Args:
        message: The message to log
        component: Component name for log prefix (UPLOAD, ASSESSMENT, etc.)
    """
    session_logger = get_session_logger()
    
    # Ensure we have an active session
    if not session_logger.is_session_active():
        session_logger.get_or_create_session()
    
    session_logger.log_message(message, component)


def configure_session_logging() -> bool:
    """
    Configure session logging from saved settings
    
    Returns:
        bool: True if successfully configured
    """
    try:
        from utilities.settings_dialog import SettingsDialog
        settings = SettingsDialog.get_saved_settings()
        log_folder = settings.get('cloudinary_log_folder', '')
        return get_session_logger().configure_log_folder(log_folder)
    except Exception as e:
        debug_errors(f"Failed to configure session logging from settings: {e}")
        return False