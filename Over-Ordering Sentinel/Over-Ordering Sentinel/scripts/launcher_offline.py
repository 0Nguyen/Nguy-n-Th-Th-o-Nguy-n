from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import webbrowser
import socket
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_FILE = PROJECT_ROOT / "app.py"
LOG_PATH = PROJECT_ROOT / "launcher_offline_error.log"
READY_FLAG = PROJECT_ROOT / "launcher_offline_ready.flag"
ERROR_FLAG = PROJECT_ROOT / "launcher_offline_error.flag"
LOCAL_URL = "http://127.0.0.1:8501"
HEALTH_URL = f"{LOCAL_URL}/_stcore/health"
STARTUP_TIMEOUT_SECONDS = 60
BROWSER_GRACE_SECONDS = 5
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
    try:
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(message + "\n")
    except Exception:
        pass


def _write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _remove_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass


def _is_windows() -> bool:
    return os.name == "nt"


def _create_no_window_kwargs() -> dict:
    if not _is_windows():
        return {}
    return {"creationflags": subprocess.CREATE_NO_WINDOW}


def _server_is_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def _port_is_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _start_streamlit() -> subprocess.Popen:
    env = os.environ.copy()
    env["APP_LAUNCH_MODE"] = "offline"
    env["PYTHONUTF8"] = "1"
    try:
        return subprocess.Popen(
            STREAMLIT_CMD,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **_create_no_window_kwargs(),
        )
    except OSError as exc:
        raise RuntimeError(f"Failed to start Streamlit: {exc}") from exc


def _wait_for_server(url: str, timeout: int = STARTUP_TIMEOUT_SECONDS, proc: subprocess.Popen | None = None) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(f"Streamlit exited early with code {proc.returncode}.")
        if _server_is_ready(HEALTH_URL) or _server_is_ready(url):
            return
        time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for Streamlit to become ready at {url}.")


def _find_browser(executables: list[str]) -> str | None:
    for executable in executables:
        candidate = shutil.which(executable)
        if candidate:
            return candidate
    return None


def _new_browser_profile_dir(browser_name: str) -> str:
    return tempfile.mkdtemp(prefix=f"oos-{browser_name}-")


def _cleanup_browser_profile_dir(profile_dir: str | None) -> None:
    if not profile_dir:
        return
    try:
        shutil.rmtree(profile_dir, ignore_errors=True)
    except Exception:
        pass


def _launch_app_browser(url: str) -> tuple[subprocess.Popen | None, str | None]:
    edge_candidates = [
        "msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    chrome_candidates = [
        "chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    edge = _find_browser(edge_candidates)
    if edge:
        profile_dir = _new_browser_profile_dir("edge")
        _log(f"Opening Microsoft Edge app window: {url}")
        _log("Launching browser process...")
        try:
            return subprocess.Popen(
                [
                    edge,
                    f"--app={url}",
                    "--new-window",
                    f"--user-data-dir={profile_dir}",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
                cwd=str(PROJECT_ROOT),
            ), profile_dir
        except OSError as exc:
            _cleanup_browser_profile_dir(profile_dir)
            _log(f"Microsoft Edge launch failed: {exc}")

    chrome = _find_browser(chrome_candidates)
    if chrome:
        profile_dir = _new_browser_profile_dir("chrome")
        _log(f"Opening Google Chrome app window: {url}")
        _log("Launching browser process...")
        try:
            return subprocess.Popen(
                [
                    chrome,
                    f"--app={url}",
                    "--new-window",
                    f"--user-data-dir={profile_dir}",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
                cwd=str(PROJECT_ROOT),
            ), profile_dir
        except OSError as exc:
            _cleanup_browser_profile_dir(profile_dir)
            _log(f"Google Chrome launch failed: {exc}")

    _log("Edge/Chrome not found. Falling back to the default browser.")
    _log("Launching browser process...")
    if not webbrowser.open_new(url):
        raise RuntimeError("Could not open the default browser.")
    return None, None


def _open_browser_detached(url: str) -> None:
    _log(f"Opening browser window: {url}")
    if not webbrowser.open_new(url):
        raise RuntimeError("Could not open the default browser.")


def _terminate_process(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return

    if proc.poll() is None:
        try:
            proc.terminate()
        except Exception:
            pass

        try:
            proc.wait(timeout=10)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def _terminate_process_tree(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return

    if _is_windows():
        try:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            return
        except Exception:
            pass

    _terminate_process(proc)


def _wait_for_browser_close(
    streamlit_process: subprocess.Popen | None,
    browser_process: subprocess.Popen | None,
) -> None:
    if streamlit_process is None:
        return

    if browser_process is None:
        _log("Browser process handle is unavailable. Launcher cannot auto-detect browser close in fallback mode.")
        while streamlit_process.poll() is None:
            time.sleep(1)
        return

    grace_deadline = time.time() + BROWSER_GRACE_SECONDS
    while time.time() < grace_deadline and browser_process.poll() is None and streamlit_process.poll() is None:
        time.sleep(0.2)

    if browser_process.poll() is not None:
        while streamlit_process.poll() is None:
            time.sleep(1)
        return

    while streamlit_process.poll() is None:
        if browser_process.poll() is not None:
            _log("Browser window closed. Stopping offline Streamlit process.")
            _terminate_process_tree(streamlit_process)
            break
        time.sleep(1)


def main() -> int:
    streamlit_process: subprocess.Popen | None = None
    browser_process: subprocess.Popen | None = None
    browser_profile_dir: str | None = None
    owns_streamlit_process = False

    try:
        _remove_file(READY_FLAG)
        _remove_file(ERROR_FLAG)
        _remove_file(LOG_PATH)
        _log("Starting Over-Ordering Sentinel in offline mode...")

        if not APP_FILE.exists():
            _log("APP_FILE not found: app.py")
            _write_text_file(ERROR_FLAG, "APP_FILE not found: app.py")
            return 1

        server_already_running = _server_is_ready(LOCAL_URL)
        if server_already_running:
            _log(f"Local app is already running at {LOCAL_URL}")
        elif _port_is_open("127.0.0.1", 8501):
            _log(f"Local app is already starting at {LOCAL_URL}")
            _wait_for_server(LOCAL_URL, timeout=STARTUP_TIMEOUT_SECONDS, proc=None)
        else:
            streamlit_process = _start_streamlit()
            owns_streamlit_process = True
            _wait_for_server(LOCAL_URL, timeout=STARTUP_TIMEOUT_SECONDS, proc=streamlit_process)
            _log(f"Local app is ready at {LOCAL_URL}")

        if not owns_streamlit_process:
            _open_browser_detached(LOCAL_URL)
            _log("Browser launch complete.")
            _write_text_file(READY_FLAG, "ready")
            return 0

        browser_process, browser_profile_dir = _launch_app_browser(LOCAL_URL)
        _log("Browser launch complete.")
        _write_text_file(READY_FLAG, "ready")

        _wait_for_browser_close(streamlit_process, browser_process)
        return 0
    except KeyboardInterrupt:
        _log("Stopping offline session...")
        return 0
    except Exception as exc:
        _log(f"ERROR: {exc}")
        _write_text_file(ERROR_FLAG, str(exc))
        return 1
    finally:
        if owns_streamlit_process:
            _terminate_process_tree(browser_process)
            _terminate_process_tree(streamlit_process)
            _cleanup_browser_profile_dir(browser_profile_dir)


if __name__ == "__main__":
    raise SystemExit(main())
