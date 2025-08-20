#!/usr/bin/env python3
import argparse
import socket
import threading
import os
from pathlib import Path

BUFSIZE = 4096

def recv_line(conn) -> str:
    """Read a single \n-terminated line, return without the trailing newline."""
    data = bytearray()
    while True:
        ch = conn.recv(1)
        if not ch:
            # connection closed mid-line
            if not data:
                return ""
            break
        data += ch
        if data.endswith(b"\n"):
            break
    return data.decode("utf-8", errors="replace").rstrip("\r\n")

def send_line(conn, line: str):
    conn.sendall((line + "\n").encode("utf-8"))

def safe_name(name: str) -> str:
    """Very small sanitization: no path separators, no absolute paths, no parent dirs."""
    name = name.replace("\\", "/")
    name = name.split("/")[-1]          # last segment
    # Optionally forbid empty/bad names
    if name in ("", ".", ".."):
        raise ValueError("invalid name")
    return name

def do_LIST(conn, root: Path):
    for p in sorted(root.iterdir()):
        if p.is_file():
            send_line(conn, p.name)
    send_line(conn, "END")

def recv_exact(conn, nbytes: int) -> bytes:
    data = bytearray()
    while len(data) < nbytes:
        chunk = conn.recv(min(BUFSIZE, nbytes - len(data)))
        if not chunk:
            raise ConnectionError("connection closed during body receive")
        data += chunk
    return bytes(data)

def do_PUT(conn, root: Path, name: str, size: int):
    path = root / safe_name(name)
    # Receive file body
    remaining = size
    with open(path, "wb") as f:
        while remaining > 0:
            chunk = conn.recv(min(BUFSIZE, remaining))
            if not chunk:
                raise ConnectionError("connection closed during upload")
            f.write(chunk)
            remaining -= len(chunk)
    send_line(conn, "OK")

def do_GET(conn, root: Path, name: str):
    path = root / safe_name(name)
    if not path.exists() or not path.is_file():
        send_line(conn, "ERR not-found")
        return
    size = path.stat().st_size
    send_line(conn, f"OK {size}")
    with open(path, "rb") as f:
        while True:
            chunk = f.read(BUFSIZE)
            if not chunk:
                break
            conn.sendall(chunk)

def do_DEL(conn, root: Path, name: str):
    path = root / safe_name(name)
    if path.exists() and path.is_file():
        path.unlink()
        send_line(conn, "OK")
    else:
        send_line(conn, "ERR not-found")

def handle_client(conn: socket.socket, addr, root: Path):
    try:
        while True:
            line = recv_line(conn)
            if not line:
                break  # client closed
            parts = line.split()
            if not parts:
                continue
            cmd = parts[0].upper()

            if cmd == "LIST":
                do_LIST(conn, root)

            elif cmd == "PUT":
                # Format: PUT <name> <size>
                if len(parts) != 3:
                    send_line(conn, "ERR usage: PUT <name> <size>")
                    continue
                try:
                    name = parts[1]
                    size = int(parts[2])
                    if size < 0:
                        raise ValueError
                except ValueError:
                    send_line(conn, "ERR invalid-size")
                    continue
                try:
                    do_PUT(conn, root, name, size)
                except Exception as e:
                    try:
                        send_line(conn, f"ERR {type(e).__name__}")
                    except Exception:
                        pass

            elif cmd == "GET":
                # Format: GET <name>
                if len(parts) != 2:
                    send_line(conn, "ERR usage: GET <name>")
                    continue
                try:
                    do_GET(conn, root, parts[1])
                except Exception as e:
                    try:
                        send_line(conn, f"ERR {type(e).__name__}")
                    except Exception:
                        pass

            elif cmd == "DEL":
                # Format: DEL <name>
                if len(parts) != 2:
                    send_line(conn, "ERR usage: DEL <name>")
                    continue
                try:
                    do_DEL(conn, root, parts[1])
                except Exception as e:
                    try:
                        send_line(conn, f"ERR {type(e).__name__}")
                    except Exception:
                        pass

            else:
                send_line(conn, "ERR unknown-cmd")
    except Exception:
        # avoid crashing the server on one bad client
        pass
    finally:
        conn.close()

def main():
    ap = argparse.ArgumentParser(description="Simple file server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=6001)
    ap.add_argument("--root", type=Path, default=Path("server_storage"),
                    help="Directory to store files")
    args = ap.parse_args()

    args.root.mkdir(parents=True, exist_ok=True)

    with socket.create_server((args.host, args.port), reuse_port=False) as srv:
        print(f"Serving on {args.host}:{args.port}, root={args.root.resolve()}")
        while True:
            conn, addr = srv.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr, args.root), daemon=True)
            t.start()

if __name__ == "__main__":
    main()
