import os
import json
from datetime import datetime

class TenantLogger:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.system_log_file = os.path.join(log_dir, "system.log")
        self.private_log_file = os.path.join(log_dir, "private.log")
        self.group_log_file = os.path.join(log_dir, "group.log")
        self.trace_log_file = os.path.join(log_dir, "trace.jsonl")
        
        os.makedirs(log_dir, exist_ok=True)

    def _append_log(self, file_path, message):
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {message}\n")
        except Exception as e:
            print(f"Logging error: {e}")

    def log_system(self, message):
        self._append_log(self.system_log_file, message)
        print(message)

    def log_private(self, message):
        self._append_log(self.private_log_file, message)
        print(message)

    def log_group(self, message):
        self._append_log(self.group_log_file, message)
        print(message)

    def log_trace_event(self, trace_id, event_type, payload):
        """
        记录结构化追踪日志 (JSONL 格式)
        """
        try:
            event = {
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type
            }
            event.update(payload)
            
            with open(self.trace_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            pass
