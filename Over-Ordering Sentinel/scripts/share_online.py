from __future__ import annotations

import argparse
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / ".local-tools"
CLOUDFLARED_DIR = TOOLS_DIR / "cloudflared"
CLOUDFLARED_EXE = CLOUDFLARED_DIR / "cloudflared.exe"

CLOUDFLARED_WINDOWS_AMD64_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
)

LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 8501
LOCAL_URL = f"http://localhost:{LOCAL_PORT}"


def log(message: str) -> None:
    print(message, flush=True)


def is_windows() -> bool:
    return os.name == "nt"


def is_port_open(host: str, port: int, timeout: float = 0.8) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def download_file(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = output_path.with_suffix(".download")

    log("")
    log("Downloading cloudflared portable executable...")
    log(f"Source: {url}")
    log(f"Target: {output_path}")
    log("")

    with urllib.request.urlopen(url) as response:
        total = response.headers.get("Content-Length")
        total_size = int(total) if total and total.isdigit() else 0

        downloaded = 0
        chunk_size = 1024 * 1024

        with open(temp_path, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break

                f.write(chunk)
                downloaded += len(chunk)

                if total_size > 0:
                    percent = downloaded * 100 / total_size
                    log(f"Downloaded: {percent:5.1f}%")
                else:
                    log(f"Downloaded: {downloaded / (1024 * 1024):.1f} MB")

    if output_path.exists():
        output_path.unlink()

    temp_path.rename(output_path)


def ensure_cloudflared() -> Path:
    if not is_windows():
        raise RuntimeError("This no-install launcher currently supports Windows only.")

    if CLOUDFLARED_EXE.exists():
        log(f"cloudflared found: {CLOUDFLARED_EXE}")
        return CLOUDFLARED_EXE

    download_file(CLOUDFLARED_WINDOWS_AMD64_URL, CLOUDFLARED_EXE)

    if not CLOUDFLARED_EXE.exists():
        raise RuntimeError("Failed to download cloudflared.exe.")

    log(f"cloudflared ready: {CLOUDFLARED_EXE}")
    return CLOUDFLARED_EXE


def start_streamlit_if_needed(password: str | None = None) -> subprocess.Popen | None:
    if is_port_open(LOCAL_HOST, LOCAL_PORT):
        log(f"Streamlit already appears to be running at {LOCAL_URL}")
        return None

    log("Starting Streamlit local server...")

    env = os.environ.copy()
    if password:
        env["APP_ACCESS_PASSWORD"] = password

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.address=localhost",
        f"--server.port={LOCAL_PORT}",
        "--server.headless=true",
    ]

    process = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    deadline = time.time() + 30
    while time.time() < deadline:
        if is_port_open(LOCAL_HOST, LOCAL_PORT):
            log(f"Streamlit is running at {LOCAL_URL}")
            return process

        if process.poll() is not None:
            raise RuntimeError("Streamlit stopped before opening port 8501.")

        time.sleep(0.5)

    raise RuntimeError("Timed out waiting for Streamlit to start.")


def copy_to_clipboard(text: str) -> bool:
    if not is_windows():
        return False

    try:
        subprocess.run(
            "clip",
            input=text,
            text=True,
            shell=True,
            check=True,
        )
        return True
    except Exception:
        return False


def start_cloudflare_tunnel(cloudflared_exe: Path) -> subprocess.Popen:
    log("Starting Cloudflare Quick Tunnel...")

    cmd = [
        str(cloudflared_exe),
        "tunnel",
        "--url",
        LOCAL_URL,
    ]

    return subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def run_share(password: str | None = None) -> int:
    log("=====================================================")
    log("Over-Ordering Sentinel - Share Online No Install")
    log("=====================================================")
    log("")
    log("This will:")
    log("1. Run the Streamlit app locally.")
    log("2. Download cloudflared portable if missing.")
    log("3. Create a temporary public HTTPS link.")
    log("4. Copy the link to clipboard when detected.")
    log("")
    log("Keep this window open. Closing it stops the public link.")
    log("")

    cloudflared_exe = ensure_cloudflared()
    streamlit_process = start_streamlit_if_needed(password=password)
    tunnel_process = start_cloudflare_tunnel(cloudflared_exe)

    url_regex = re.compile(r"https://[a-zA-Z0-9-]+\\.trycloudflare\\.com")
    public_url = None

    try:
        assert tunnel_process.stdout is not None

        for line in tunnel_process.stdout:
            clean_line = line.rstrip()
            print(clean_line, flush=True)

            match = url_regex.search(clean_line)
            if match and public_url is None:
                public_url = match.group(0)

                log("")
                log("=====================================================")
                log("PUBLIC LINK READY")
                log("=====================================================")
                log(public_url)
                log("=====================================================")
                log("Send this link to your sister/tester.")
                log("She does NOT need to install anything.")
                log("Your computer and this window must stay open.")
                log("=====================================================")
                log("")

                if copy_to_clipboard(public_url):
                    log("The public link was copied to clipboard.")
                else:
                    log("Could not copy automatically. Copy the link manually.")

        return tunnel_process.wait()

    except KeyboardInterrupt:
        log("")
        log("Stopping temporary share...")
        return 0

    finally:
        try:
            tunnel_process.terminate()
        except Exception:
            pass

        if streamlit_process is not None:
            try:
                streamlit_process.terminate()
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--password",
        default="",
        help="Optional password for APP_ACCESS_PASSWORD.",
    )

    args = parser.parse_args()
    password = args.password.strip() or None

    try:
        return run_share(password=password)
    except Exception as exc:
        log("")
        log("ERROR:")
        log(str(exc))
        log("")
        log("Press Enter to close.")
        try:
            input()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
