from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_URL = "http://127.0.0.1:8501/?launcher=online_admin"
STREAMLIT_CMD = [
    sys.executable,
    "-m",
    "streamlit",
    "run",
    "app.py",
    "--server.address=127.0.0.1",
    "--server.port=8501",
    "--server.headless=true",
]


def _log(message: str) -> None:
    print(message, flush=True)


def _create_no_window_kwargs() -> dict:
    if os.name != "nt":
        return {}
    return {"creationflags": subprocess.CREATE_NO_WINDOW}


def _free_port_8501() -> None:
    if os.name != "nt":
        return

    try:
        result = subprocess.run(
            "netstat -ano | findstr :8501",
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        pids = set()
        for line in result.stdout.splitlines():
            parts = line.split()
            if not parts:
                continue
            pid = parts[-1]
            if pid.isdigit():
                pids.add(pid)
        for pid in pids:
            subprocess.run(
                ["taskkill", "/PID", pid, "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
    except Exception:
        pass


def _start_streamlit() -> subprocess.Popen:
    env = os.environ.copy()
    env["APP_LAUNCH_MODE"] = "online_admin"
    env["PYTHONUTF8"] = "1"
    return subprocess.Popen(
        STREAMLIT_CMD,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **_create_no_window_kwargs(),
    )


def _wait_for_server(url: str, timeout: int = 60, proc: subprocess.Popen | None = None) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(f"Streamlit exited early with code {proc.returncode}.")
        try:
            with urllib.request.urlopen(url, timeout=2):
                return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for Streamlit to become ready at {url}.")


def _open_browser(url: str) -> None:
    webbrowser.open_new(url)


def _terminate_process(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return

    if proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def main() -> int:
    streamlit_process: subprocess.Popen | None = None

    try:
        _log("Starting Over-Ordering Sentinel in online admin mode...")
        _log("Local app will run at http://127.0.0.1:8501")
        _free_port_8501()
        streamlit_process = _start_streamlit()
        _wait_for_server("http://127.0.0.1:8501", timeout=60, proc=streamlit_process)
        _open_browser(LOCAL_URL)
        _log("Streamlit is running. Use the admin panel inside the app to create or stop a share link.")

        while streamlit_process.poll() is None:
            time.sleep(1)

        return streamlit_process.returncode or 0
    except KeyboardInterrupt:
        _log("Stopping online admin session...")
        return 0
    except Exception as exc:
        _log(f"ERROR: {exc}")
        return 1
    finally:
        _terminate_process(streamlit_process)


if __name__ == "__main__":
    raise SystemExit(main())
