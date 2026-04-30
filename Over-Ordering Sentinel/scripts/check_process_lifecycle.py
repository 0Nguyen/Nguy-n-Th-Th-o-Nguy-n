"""
Check process lifecycle for Over-Ordering Sentinel (Windows).
Produces a simple report used by the manual test steps in docs/PROCESS_LIFECYCLE_TEST.txt.

Usage (run from project root):
    python scripts/check_process_lifecycle.py
    or
    py scripts/check_process_lifecycle.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import json
from typing import List, Dict

PROJECT_ROOT = os.path.abspath(os.getcwd())
CHECK_PIDS: List[Dict[str, str]] = []


def run_cmd(cmd: List[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        try:
            return out.decode("utf-8", errors="ignore")
        except Exception:
            return out.decode(errors="ignore")
    except subprocess.CalledProcessError as exc:
        try:
            return exc.output.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    except Exception:
        return ""


def wmic_process_list() -> List[Dict[str, str]]:
    """Return list of processes as dicts with keys 'pid' and 'cmdline'."""
    ps_cmd = (
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,CommandLine | "
        "ConvertTo-Json -Compress -Depth 2"
    )
    out = run_cmd(["powershell", "-NoProfile", "-Command", ps_cmd]).strip()
    if out:
        try:
            parsed = json.loads(out)
            if isinstance(parsed, dict):
                parsed = [parsed]
            results: List[Dict[str, str]] = []
            for item in parsed:
                pid = str(item.get("ProcessId", "") or "")
                cmdline = str(item.get("CommandLine", "") or "")
                if pid or cmdline:
                    results.append({"pid": pid, "cmdline": cmdline})
            if results:
                return results
        except Exception:
            pass

    out = run_cmd(["wmic", "process", "get", "ProcessId,CommandLine", "/FORMAT:LIST"])
    lines = [ln.strip() for ln in out.splitlines()]
    results = []
    current = {"pid": "", "cmdline": ""}
    for ln in lines:
        if not ln:
            if current["pid"] or current["cmdline"]:
                results.append(current.copy())
                current = {"pid": "", "cmdline": ""}
            continue
        if ln.startswith("CommandLine="):
            current["cmdline"] = ln.partition("=")[2]
        elif ln.startswith("ProcessId="):
            current["pid"] = ln.partition("=")[2]
    if current["pid"] or current["cmdline"]:
        results.append(current.copy())
    return results


def netstat_lines() -> List[str]:
    out = run_cmd(["netstat", "-ano"])
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def is_port_listening(port: int, netstat: List[str]) -> bool:
    needle = f":{port} "
    for ln in netstat:
        if needle in ln and "LISTEN" in ln.upper():
            return True
    return False


def find_processes_of_interest(procs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    keywords = ["app.py", "online_admin_app.py", "cloudflared", PROJECT_ROOT.replace("\\", "\\\\")]
    found: List[Dict[str, str]] = []
    for p in procs:
        cmd = (p.get("cmdline") or "").lower()
        for kw in keywords:
            if kw.lower() in cmd:
                found.append({"pid": p.get("pid", ""), "cmdline": p.get("cmdline", "")})
                break
    return found


def count_cloudflared(procs: List[Dict[str, str]]) -> int:
    total = 0
    for p in procs:
        cmd = (p.get("cmdline") or "").lower()
        if "cloudflared" in cmd:
            total += 1
    return total


def main() -> int:
    procs = wmic_process_list()
    net = netstat_lines()

    cloudflared_count = count_cloudflared(procs)
    cloudflared_running = "yes" if cloudflared_count > 0 else "no"
    backend_listening = "yes" if is_port_listening(8501, net) else "no"
    admin_listening = "yes" if is_port_listening(8502, net) else "no"

    related = find_processes_of_interest(procs)

    print("--- Over-Ordering Sentinel process lifecycle check ---")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"cloudflared running: {cloudflared_running}")
    print(f"backend 8501 listening: {backend_listening}")
    print(f"admin 8502 listening: {admin_listening}")
    print("")
    print("Related processes (command line contains app.py, online_admin_app.py, cloudflared, or project path):")
    if related:
        for p in related:
            print(f"- PID: {p.get('pid') or '<unknown>'}  CMD: {p.get('cmdline')}")
    else:
        print("- (none found)")

    print("")
    print("Debug helpers:")
    print("- To list all processes with command line: wmic process get ProcessId,CommandLine")
    print("- To see listening ports: netstat -ano | findstr :8501")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
