from collections import deque
from datetime import datetime
from typing import List, Dict
import threading

class LogBuffer:
    """Thread-safe circular buffer for storing recent log messages"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.logs = deque(maxlen=max_size)
        self.lock = threading.Lock()

    def add(self, level: str, message: str, context: str = ""):
        """Add a log message to the buffer"""
        with self.lock:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
                "context": context
            }
            self.logs.append(log_entry)

    def get_recent(self, count: int = 50) -> List[Dict]:
        """Get the most recent log messages"""
        with self.lock:
            # Return last 'count' messages
            return list(self.logs)[-count:]

    def clear(self):
        """Clear all logs"""
        with self.lock:
            self.logs.clear()

# Global log buffer instance
log_buffer = LogBuffer(max_size=200)

def log_info(message: str, context: str = ""):
    """Log an info message"""
    log_buffer.add("INFO", message, context)
    print(f"[INFO] {context}: {message}" if context else f"[INFO] {message}")

def log_warning(message: str, context: str = ""):
    """Log a warning message"""
    log_buffer.add("WARNING", message, context)
    print(f"[WARNING] {context}: {message}" if context else f"[WARNING] {message}")

def log_error(message: str, context: str = ""):
    """Log an error message"""
    log_buffer.add("ERROR", message, context)
    print(f"[ERROR] {context}: {message}" if context else f"[ERROR] {message}")

def log_success(message: str, context: str = ""):
    """Log a success message"""
    log_buffer.add("SUCCESS", message, context)
    print(f"[SUCCESS] {context}: {message}" if context else f"[SUCCESS] {message}")
