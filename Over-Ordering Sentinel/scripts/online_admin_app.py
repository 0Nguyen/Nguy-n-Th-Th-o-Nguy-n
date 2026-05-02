from __future__ import annotations

import os
import subprocess
import sys
import time
import atexit
import urllib.request
from pathlib import Path

import streamlit as st

from scripts.share_tunnel import inspect_cloudflared_status, start_cloudflare_tunnel, stop_tunnel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_URL = "http://127.0.0.1:8503"
ADMIN_URL = "http://127.0.0.1:8502"
STREAMLIT_BACKEND_CMD = [
    sys.executable,
    "-m",
    "streamlit",
    "run",
    "app.py",
    "--server.address=127.0.0.1",
    "--server.port=8503",
    "--server.headless=true",
]


def _no_window_kwargs() -> dict:
    if os.name != "nt":
        return {}
    return {"creationflags": subprocess.CREATE_NO_WINDOW}


def _is_running(proc: subprocess.Popen | None) -> bool:
    return proc is not None and proc.poll() is None


def _tunnel_state() -> tuple[subprocess.Popen | None, int | None]:
    proc = st.session_state.get("tunnel_proc")
    pid = st.session_state.get("tunnel_pid")
    try:
        pid_value = int(pid) if pid is not None else None
    except Exception:
        pid_value = None
    return proc if isinstance(proc, subprocess.Popen) else None, pid_value


def _safe_terminate(proc: subprocess.Popen | None) -> None:
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


def _pid_is_running(pid: int | None) -> bool:
    if pid is None or pid <= 0 or os.name != "nt":
        return False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout or result.stderr or "").strip().lower()
        return bool(output) and "no tasks are running" not in output and str(pid) in output
    except Exception:
        return False


def stop_process(proc: subprocess.Popen | None) -> None:
    _safe_terminate(proc)


def wait_until_ready(url: str, timeout: int = 60, proc: subprocess.Popen | None = None) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(f"Process exited early with code {proc.returncode}.")
        try:
            with urllib.request.urlopen(url, timeout=2):
                return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}.")


def _current_password() -> str:
    return str(st.session_state.get("current_password", "")).strip()


def _random_password(length: int = 10) -> str:
    import secrets
    import string

    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def start_backend_app(password: str | None) -> subprocess.Popen:
    env = os.environ.copy()
    env.pop("APP_LAUNCH_MODE", None)
    env.pop("APP_ACCESS_PASSWORD", None)
    if password:
        env["APP_ACCESS_PASSWORD"] = password
    env["PYTHONUTF8"] = "1"
    return subprocess.Popen(
        STREAMLIT_BACKEND_CMD,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **_no_window_kwargs(),
    )


def _backend_status() -> str:
    proc = st.session_state.get("backend_proc")
    if _is_running(proc):
        return "running"
    try:
        with urllib.request.urlopen(BACKEND_URL, timeout=2):
            return "running"
    except Exception:
        return "stopped"


def _ensure_backend_running() -> None:
    proc = st.session_state.get("backend_proc")
    if _is_running(proc):
        return
    if _backend_status() == "running" and proc is None:
        return

    password = _current_password() or None
    proc = start_backend_app(password)
    st.session_state["backend_proc"] = proc
    wait_until_ready(BACKEND_URL, timeout=60, proc=proc)


def _restart_backend() -> None:
    stop_process(st.session_state.get("backend_proc"))
    st.session_state.pop("backend_proc", None)
    _ensure_backend_running()


def _stop_backend() -> None:
    stop_process(st.session_state.get("backend_proc"))
    st.session_state.pop("backend_proc", None)


def _ensure_tunnel_stopped() -> None:
    proc, pid = _tunnel_state()
    success, message = stop_tunnel(proc, pid=pid)
    if success:
        st.session_state.pop("tunnel_proc", None)
        st.session_state.pop("tunnel_pid", None)
        st.session_state.pop("public_url", None)
        st.session_state.pop("cloudflared_path", None)
        st.session_state.pop("tunnel_metadata", None)
        st.session_state.pop("last_tunnel_stop_error", None)
    else:
        st.session_state["last_tunnel_stop_error"] = message


def _create_public_link() -> None:
    _ensure_backend_running()
    proc, pid = _tunnel_state()
    if _is_running(proc) or _pid_is_running(pid):
        st.session_state.setdefault("public_url", "")
        return

    if pid is not None and proc is None:
        _ensure_tunnel_stopped()

    tunnel = start_cloudflare_tunnel(BACKEND_URL)
    st.session_state["tunnel_proc"] = tunnel["process"]
    st.session_state["tunnel_pid"] = tunnel["pid"]
    st.session_state["public_url"] = tunnel["public_url"]
    st.session_state["cloudflared_path"] = tunnel["cloudflared_path"]
    st.session_state["tunnel_metadata"] = {
        "cloudflared_path": tunnel["cloudflared_path"],
        "pid": tunnel["pid"],
    }
    st.session_state.pop("last_tunnel_stop_error", None)


def _render_cloudflared_check() -> None:
    status = inspect_cloudflared_status()
    with st.expander("Kiểm tra Cloudflare Tunnel / Cloudflared check", expanded=False):
        st.write(f"tools/cloudflared.exe exists: `{status['tools_exists']}`")
        st.write(f"cloudflared in PATH: `{status['path_exists']}`")
        st.write(f"active cloudflared path: `{status['tool_path'] or '<none>'}`")
        st.write(f"version: `{status['version'] or '<unavailable>'}`")
        st.write(f"status: `{status['status']}`")


def _render_password_controls() -> None:
    options = [
        "Không dùng mật khẩu / No password",
        "Tự tạo mật khẩu / Generate password",
        "Nhập mật khẩu thủ công / Custom password",
    ]
    if "password_mode" not in st.session_state:
        st.session_state["password_mode"] = options[0]
    mode = st.radio("Password mode", options=options, key="password_mode")

    if mode == options[0]:
        st.session_state["current_password"] = ""
        st.caption("No password.")
    elif mode == options[1]:
        if st.button("Generate password", use_container_width=True):
            st.session_state["current_password"] = _random_password(10)
        if st.session_state.get("current_password"):
            st.code(st.session_state["current_password"], language="text")
    else:
        st.session_state["current_password"] = st.text_input(
            "Custom password",
            value=st.session_state.get("current_password", ""),
            type="password",
            key="custom_password_input",
        ).strip()

    if st.button("Apply password and restart backend", use_container_width=True):
        _restart_backend()
        st.success("Backend restarted.")


def _render_backend_controls() -> None:
    st.subheader("A. Backend app status")
    st.write(f"Backend app URL: {BACKEND_URL}")
    st.write(f"Backend status: {_backend_status()}")

    if st.button("▶ Start backend app", use_container_width=True):
        _ensure_backend_running()
        st.success("Backend started.")

    if st.button("🔄 Restart backend app", use_container_width=True):
        _restart_backend()
        st.success("Backend restarted.")

    if st.button("🛑 Stop backend app", use_container_width=True):
        _stop_backend()
        st.info("Backend stopped.")


def _render_share_controls() -> None:
    st.subheader("D. Share link control")
    if st.button("🚀 Create public share link", use_container_width=True):
        try:
            _create_public_link()
            st.success("Public link created.")
        except Exception as exc:
            st.error(str(exc))

    if st.button("🛑 Stop public share link", use_container_width=True):
        _ensure_tunnel_stopped()
        if st.session_state.get("last_tunnel_stop_error"):
            st.error(st.session_state["last_tunnel_stop_error"])
        else:
            st.success("Public share link stopped.")

    public_url = st.session_state.get("public_url", "")
    if public_url:
        st.write("PUBLIC SHARE LINK:")
        st.code(public_url, language="text")
    if _current_password():
        st.write("PASSWORD:")
        st.code(_current_password(), language="text")


def _cleanup() -> None:
    _ensure_tunnel_stopped()
    _stop_backend()


atexit.register(_cleanup)


def main() -> None:
    st.set_page_config(page_title="Over-Ordering Sentinel - Online Admin", layout="wide")
    st.title("🌐 Over-Ordering Sentinel - Online Admin")
    st.caption(
        "App chính sẽ chạy ở backend tại http://127.0.0.1:8503. "
        "Public link sẽ trỏ vào app chính. Public user sẽ thấy giao diện app bình thường, không thấy admin."
    )

    st.info("Admin page chỉ local ở 127.0.0.1:8502. Public link chỉ trỏ vào app chính, không trỏ vào admin.")

    _render_backend_controls()
    st.divider()
    st.subheader("B. Password setup")
    _render_password_controls()
    st.divider()
    st.subheader("C. Cloudflared status")
    _render_cloudflared_check()
    st.divider()
    _render_share_controls()
    st.warning(
        "Đây là link tạm thời. Không upload dữ liệu bệnh viện thật nếu chưa kiểm soát bảo mật. "
        "Tắt CMD hoặc tắt máy thì link chết. Admin page chỉ local ở 127.0.0.1:8502."
    )


if __name__ == "__main__":
    main()
