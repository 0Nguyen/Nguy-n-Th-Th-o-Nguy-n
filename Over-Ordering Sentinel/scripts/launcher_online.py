from __future__ import annotations

import atexit
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADMIN_URL = "http://127.0.0.1:8502"
STREAMLIT_CMD = [
    sys.executable,
    "-m",
    "streamlit",
    "run",
    "scripts/online_admin_app.py",
    "--server.address=127.0.0.1",
    "--server.port=8502",
    "--server.headless=true",
]


def _log(message: str) -> None:
    print(message, flush=True)


def _is_windows() -> bool:
    return os.name == "nt"


def _create_no_window_kwargs() -> dict:
    if not _is_windows():
        return {}
    return {"creationflags": subprocess.CREATE_NO_WINDOW}


def _start_admin() -> subprocess.Popen:
    return subprocess.Popen(
        STREAMLIT_CMD,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONUTF8": "1"},
        **_create_no_window_kwargs(),
    )


def _wait_for_server(url: str, timeout: int = 60, proc: subprocess.Popen | None = None) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(f"Admin Streamlit exited early with code {proc.returncode}.")
        try:
            with urllib.request.urlopen(url, timeout=2):
                return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for admin Streamlit at {url}.")


def _open_browser(url: str) -> None:
    webbrowser.open_new(url)


def _terminate_process(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    if proc.poll() is None:
        try:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


global_admin_proc: subprocess.Popen | None = None


def _cleanup_on_exit() -> None:
    """Cleanup handler called when launcher exits."""
    global global_admin_proc
    if global_admin_proc is not None:
        _log("Cleaning up processes...")
        _terminate_process(global_admin_proc)
        time.sleep(1)  # Give processes time to clean up
        _log("Cleanup complete.")


def main() -> int:
    global global_admin_proc
    admin_proc: subprocess.Popen | None = None
    try:
        _log("Starting Over-Ordering Sentinel online admin...")
        admin_proc = _start_admin()
        global_admin_proc = admin_proc
        atexit.register(_cleanup_on_exit)
        _wait_for_server(ADMIN_URL, timeout=60, proc=admin_proc)
        _open_browser(ADMIN_URL)
        _log("Admin console is running at http://127.0.0.1:8502")
        while admin_proc.poll() is None:
            time.sleep(1)
        return admin_proc.returncode or 0
    except KeyboardInterrupt:
        _log("Stopping online admin...")
        return 0
    except Exception as exc:
        _log(f"ERROR: {exc}")
        return 1
    finally:
        _terminate_process(admin_proc)


if __name__ == "__main__":
    raise SystemExit(main())
