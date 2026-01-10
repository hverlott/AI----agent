import json
import time
import psutil
from pathlib import Path

def sample_system(samples=10, interval=1.0):
    pids = []
    for p in psutil.process_iter(['name']):
        name = (p.info.get('name') or '').lower()
        if 'python' in name or 'streamlit' in name:
            pids.append(p.pid)
    out = []
    for _ in range(samples):
        s = {
            "t": time.time(),
            "cpu_pct": psutil.cpu_percent(interval=interval),
            "mem": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage('/')._asdict() if hasattr(psutil, 'disk_usage') else {},
        }
        procs = []
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                procs.append({
                    "pid": pid,
                    "name": proc.name(),
                    "cpu_pct": proc.cpu_percent(interval=None),
                    "rss": proc.memory_info().rss,
                    "vms": proc.memory_info().vms,
                    "threads": proc.num_threads(),
                })
            except Exception:
                continue
        s["procs"] = procs
        out.append(s)
    return out

def main():
    data = sample_system(samples=10, interval=0.5)
    out_path = Path(__file__).parent / "perf_report.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Perf report saved: {out_path}")

if __name__ == "__main__":
    main()
