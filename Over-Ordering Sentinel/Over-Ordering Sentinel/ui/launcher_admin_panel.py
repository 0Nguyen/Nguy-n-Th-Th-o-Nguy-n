from __future__ import annotations

import os
import secrets
import string

import streamlit as st

from scripts.share_tunnel import inspect_cloudflared_status, start_cloudflare_tunnel, stop_tunnel


LOCAL_URL = "http://127.0.0.1:8501"
PASSWORD_KEY = "APP_ACCESS_PASSWORD_RUNTIME"
TUNNEL_PROCESS_KEY = "launcher_share_tunnel_process"
TUNNEL_URL_KEY = "launcher_share_public_url"
PASSWORD_MODE_KEY = "launcher_password_mode"
CUSTOM_PASSWORD_KEY = "launcher_custom_password"


def _random_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _current_password() -> str:
    runtime_password = str(st.session_state.get(PASSWORD_KEY, "")).strip()
    if runtime_password:
        return runtime_password
    return os.getenv("APP_ACCESS_PASSWORD", "").strip()


def _clear_runtime_password() -> None:
    st.session_state.pop(PASSWORD_KEY, None)


def _set_runtime_password(password: str) -> None:
    st.session_state[PASSWORD_KEY] = password.strip()


def is_online_admin_mode() -> bool:
    env_mode = os.getenv("APP_LAUNCH_MODE", "").strip().lower()

    query_mode = ""
    try:
        query_mode = st.query_params.get("launcher", "")
    except Exception:
        query_mode = ""

    if isinstance(query_mode, list):
        query_mode = query_mode[0] if query_mode else ""

    query_mode = str(query_mode).strip().lower()

    return env_mode == "online_admin" or query_mode == "online_admin"


def _handle_password_controls(current_password: str) -> None:
    options = [
        "Không dùng mật khẩu / No password",
        "Tự tạo mật khẩu / Generate password",
        "Nhập mật khẩu thủ công / Custom password",
    ]
    current_mode = st.session_state.get(PASSWORD_MODE_KEY)
    if current_mode not in options:
        current_mode = options[0] if not current_password else options[2]

    mode = st.radio("Password mode", options=options, index=options.index(current_mode), key=PASSWORD_MODE_KEY)

    if mode == options[0]:
        _clear_runtime_password()
        st.caption("No password will be used for new share sessions in this browser session.")
        return

    if mode == options[1]:
        if st.button("Generate password", use_container_width=True):
            generated = _random_password(10)
            _set_runtime_password(generated)
            st.code(generated, language="text")
        if PASSWORD_KEY in st.session_state:
            st.code(st.session_state[PASSWORD_KEY], language="text")
        st.caption(
            "Password mới sẽ áp dụng cho link share trong phiên này nếu auth_gate hỗ trợ session password. "
            "Nếu chưa hỗ trợ, cần restart bằng START_SHARE_ONLINE_NO_INSTALL_PASSWORD.bat."
        )
        return

    custom_password = st.text_input("Custom password", type="password", key=CUSTOM_PASSWORD_KEY)
    if custom_password:
        _set_runtime_password(custom_password)
    else:
        _clear_runtime_password()
    st.caption(
        "Password mới sẽ áp dụng cho link share trong phiên này nếu auth_gate hỗ trợ session password. "
        "Nếu chưa hỗ trợ, cần restart bằng START_SHARE_ONLINE_NO_INSTALL_PASSWORD.bat."
    )


def _render_tunnel_status() -> None:
    proc = st.session_state.get(TUNNEL_PROCESS_KEY)
    public_url = st.session_state.get(TUNNEL_URL_KEY, "")
    if proc is not None and getattr(proc, "poll", lambda: 1)() is not None:
        st.session_state.pop(TUNNEL_PROCESS_KEY, None)
        st.session_state.pop(TUNNEL_URL_KEY, None)
        public_url = ""

    if public_url:
        st.success("Share link is active.")
        st.code(public_url, language="text")
    else:
        st.info("Share link is not running yet.")


def _render_cloudflared_check() -> None:
    status = inspect_cloudflared_status()
    with st.expander("Kiểm tra Cloudflare Tunnel / Cloudflared check", expanded=False):
        st.write(f"tools/cloudflared.exe exists: `{status['tools_exists']}`")
        st.write(f"cloudflared in PATH exists: `{status['path_exists']}`")
        st.write(f"cloudflared_path đang dùng: `{status['tool_path'] or '<none>'}`")
        st.write(f"version: `{status['version'] or '<unavailable>'}`")
        st.write(f"trạng thái cài đặt: `{status['status']}`")
        st.write(f"available_local: `{status['available_local']}`")
        st.write(f"available_path: `{status['available_path']}`")
        st.write(f"installed_by_winget: `{status['installed_by_winget']}`")
        st.write(f"downloaded_to_tools: `{status['downloaded_to_tools']}`")


def _manual_fix_text() -> str:
    return (
        "Không tìm thấy hoặc không thể dùng cloudflared. "
        "Hãy thử CMD: `winget install --id Cloudflare.cloudflared`. "
        "Hoặc tải `cloudflared-windows-amd64.exe`, đổi tên thành `cloudflared.exe`, "
        "rồi đặt vào `tools/cloudflared.exe`."
    )


def render_launcher_admin_panel() -> None:
    if not is_online_admin_mode():
        return

    with st.container(border=True):
        st.markdown("## 🌐 Online Share Admin")
        st.caption("App đang chạy trên máy của bạn. Bạn có thể tạo link public tạm thời để người khác truy cập.")

        st.info(f"Local app: {LOCAL_URL}")
        st.write("Launch mode: `online_admin`")
        st.write(f"Password status: {'Protected' if _current_password() else 'No password'}")

        _render_cloudflared_check()

        st.markdown("**Password mode**")
        _handle_password_controls(_current_password())

        st.markdown("**Share link**")
        _render_tunnel_status()

        create_clicked = st.button(
            "🚀 Tạo link share online / Create public share link",
            use_container_width=True,
        )
        stop_clicked = st.button(
            "🛑 Tắt link share / Stop sharing",
            use_container_width=True,
        )

        if create_clicked:
            status = inspect_cloudflared_status()
            if status["available_local"] or status["available_path"]:
                st.info("Cloudflared đã có sẵn. Đang tạo link...")
            else:
                st.info("Chưa tìm thấy cloudflared. Đang thử cài bằng winget...")

            try:
                tunnel = start_cloudflare_tunnel(LOCAL_URL)
                st.session_state[TUNNEL_PROCESS_KEY] = tunnel["process"]
                st.session_state[TUNNEL_URL_KEY] = tunnel["public_url"]
                st.success("Public link created.")
                st.code(tunnel["public_url"], language="text")
                if _current_password():
                    st.code(_current_password(), language="text")
                st.warning("Giữ cửa sổ CMD mở. Tắt CMD hoặc tắt máy thì link sẽ chết.")
            except Exception as exc:
                st.error(f"{exc}")
                st.error(_manual_fix_text())

        if stop_clicked:
            proc = st.session_state.pop(TUNNEL_PROCESS_KEY, None)
            st.session_state.pop(TUNNEL_URL_KEY, None)
            stop_tunnel(proc)
            st.info("Share link stopped.")

        st.warning(
            "Đây là link tạm thời. Không upload dữ liệu bệnh viện thật nếu chưa kiểm soát bảo mật. "
            "Tắt CMD hoặc tắt máy thì link chết."
        )
