from __future__ import annotations

import queue
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
CLOUDFLARED_EXE = TOOLS_DIR / "cloudflared.exe"
CLOUDFLARED_DOWNLOAD_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
)


def is_executable_working(path: str) -> bool:
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def _version_output(path: str) -> str:
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        output = (result.stdout or result.stderr or "").strip()
        if result.returncode == 0 and output:
            return output
    except Exception:
        pass
    return ""


def download_cloudflared_to_tools() -> str:
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = Path(str(CLOUDFLARED_EXE) + ".tmp")

    try:
        with urllib.request.urlopen(CLOUDFLARED_DOWNLOAD_URL, timeout=30) as response, open(temp_path, "wb") as handle:
            shutil.copyfileobj(response, handle)

        if CLOUDFLARED_EXE.exists():
            CLOUDFLARED_EXE.unlink()
        temp_path.replace(CLOUDFLARED_EXE)

        if not is_executable_working(str(CLOUDFLARED_EXE)):
            raise RuntimeError("cloudflared.exe vừa tải về nhưng chạy `--version` thất bại.")

        return str(CLOUDFLARED_EXE)
    except Exception:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        raise


def _winget_install_cloudflared() -> bool:
    try:
        result = subprocess.run(
            [
                "winget",
                "install",
                "--id",
                "Cloudflare.cloudflared",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def inspect_cloudflared_status() -> dict:
    local_exists = CLOUDFLARED_EXE.exists()
    local_working = local_exists and is_executable_working(str(CLOUDFLARED_EXE))
    path_exe = shutil.which("cloudflared.exe") or shutil.which("cloudflared") or ""
    path_working = bool(path_exe) and is_executable_working(path_exe)
    tool_path = ""
    available_local = False
    available_path = False
    installed_by_winget = False
    downloaded_to_tools = False

    if local_working:
        tool_path = str(CLOUDFLARED_EXE)
        available_local = True
    elif path_working:
        tool_path = path_exe
        available_path = True

    return {
        "tools_exists": local_exists,
        "tools_working": local_working,
        "path_exists": bool(path_exe),
        "path_working": path_working,
        "tool_path": tool_path,
        "available_local": available_local,
        "available_path": available_path,
        "installed_by_winget": installed_by_winget,
        "downloaded_to_tools": downloaded_to_tools,
        "status": "available_local" if available_local else "available_path" if available_path else "unavailable",
        "version": _version_output(tool_path) if tool_path else "",
    }


def ensure_cloudflared() -> str:
    if CLOUDFLARED_EXE.exists() and is_executable_working(str(CLOUDFLARED_EXE)):
        return str(CLOUDFLARED_EXE)

    path_exe = shutil.which("cloudflared.exe") or shutil.which("cloudflared")
    if path_exe and is_executable_working(path_exe):
        return path_exe

    if _winget_install_cloudflared():
        path_exe = shutil.which("cloudflared.exe") or shutil.which("cloudflared")
        if path_exe and is_executable_working(path_exe):
            return path_exe

    downloaded_path = download_cloudflared_to_tools()
    if downloaded_path and is_executable_working(downloaded_path):
        return downloaded_path

    raise RuntimeError(
        "Không tìm thấy và không thể tự cài cloudflared. Hãy cài bằng lệnh: "
        "winget install --id Cloudflare.cloudflared hoặc tải cloudflared.exe thủ công rồi đặt vào thư mục tools/cloudflared.exe"
    )


def _spawn_reader(proc: subprocess.Popen, output_queue: queue.Queue[str]) -> threading.Thread:
    def _reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            output_queue.put(line.rstrip())
        output_queue.put("")

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
    return thread


def start_cloudflare_tunnel(local_url: str) -> dict:
    cloudflared_path = ensure_cloudflared()
    proc = subprocess.Popen(
        [cloudflared_path, "tunnel", "--url", local_url],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    output_queue: queue.Queue[str] = queue.Queue()
    _spawn_reader(proc, output_queue)

    url_pattern = re.compile(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com")
    deadline = time.time() + 60
    public_url = ""

    while time.time() < deadline:
        try:
            line = output_queue.get(timeout=0.5)
        except queue.Empty:
            if proc.poll() is not None and not public_url:
                stop_tunnel(proc)
                raise RuntimeError("cloudflared stopped trước khi tạo được link public.")
            continue

        if not line:
            if proc.poll() is not None and not public_url:
                stop_tunnel(proc)
                raise RuntimeError("cloudflared stopped trước khi tạo được link public.")
            continue

        match = url_pattern.search(line)
        if match:
            public_url = match.group(0)
            break

    if not public_url:
        stop_tunnel(proc)
        raise RuntimeError("Không lấy được link trycloudflare.com sau 60 giây.")

    return {
        "process": proc,
        "pid": proc.pid,
        "public_url": public_url,
        "cloudflared_path": cloudflared_path,
    }


def _is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False

    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except Exception:
            return False

    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout or result.stderr or "").strip().lower()
        if not output or "no tasks are running" in output:
            return False
        return str(pid) in output
    except Exception:
        return False


def stop_tunnel_by_pid(pid: int) -> bool:
    if pid <= 0:
        return True
    if not _is_pid_running(pid):
        return True

    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        pass

    return not _is_pid_running(pid)


def stop_tunnel(proc: subprocess.Popen | None, pid: int | None = None) -> tuple[bool, str]:
    if proc is None:
        if pid is None:
            return True, "Tunnel process was not running."
        success = stop_tunnel_by_pid(pid)
        return success, "Tunnel process stopped by PID." if success else f"Failed to stop tunnel PID {pid}."

    if proc.poll() is not None:
        return True, "Tunnel process had already exited."

    last_error = ""

    try:
        proc.terminate()
        proc.wait(timeout=5)
        return True, "Tunnel process terminated."
    except Exception as exc:
        last_error = str(exc)

    try:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
            return True, "Tunnel process killed."
    except Exception as exc:
        last_error = str(exc)

    fallback_pid = pid if pid is not None else getattr(proc, "pid", 0)
    if fallback_pid and stop_tunnel_by_pid(fallback_pid):
        return True, f"Tunnel process stopped by PID {fallback_pid}."

    if not last_error:
        last_error = f"Unable to stop tunnel process PID {fallback_pid or '<unknown>'}."
    return False, last_error
