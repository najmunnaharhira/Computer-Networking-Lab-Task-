#!/usr/bin/env python3
import argparse
import pathlib
import socket

BUFSIZE = 1024  # define buffer size (adjust as needed)

def recv_line(sock):
    data = b""
    while not data.endswith(b"\n"):
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("Connection closed while reading line")
        data += chunk
    return data.decode().strip()

def send_line(sock, line: str):
    sock.sendall((line + "\n").encode())

def do_list(sock):
    send_line(sock, "LIST")
    while True:
        line = recv_line(sock)
        if line == "END":
            break
        print(line)
    return 0

def do_put(sock, path: pathlib.Path):
    size = path.stat().st_size
    send_line(sock, f"PUT {path.name} {size}")
    with open(path, "rb") as f:
        while chunk := f.read(BUFSIZE):
            sock.sendall(chunk)
    res = recv_line(sock)
    print(res)
    return 0 if res == "OK" else 1

def do_get(sock, name: str, outdir: pathlib.Path):
    send_line(sock, f"GET {name}")
    first = recv_line(sock)
    if not first.startswith("OK "):
        print(first)
        return 1
    size = int(first.split()[1])
    dest = outdir / name
    received = 0
    with open(dest, "wb") as f:
        while received < size:
            chunk = sock.recv(min(BUFSIZE, size - received))
            if not chunk:
                raise ConnectionError("connection closed during download")
            f.write(chunk)
            received += len(chunk)
    print(f"Downloaded to {dest} ({size} bytes)")
    return 0

def do_del(sock, name: str):
    send_line(sock, f"DEL {name}")
    res = recv_line(sock)
    print(res)
    return 0 if res == "OK" else 1

def main():
    ap = argparse.ArgumentParser(description="File client")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=6001)

    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    p_put = sub.add_parser("put")
    p_put.add_argument("path", type=pathlib.Path)

    p_get = sub.add_parser("get")
    p_get.add_argument("name")
    p_get.add_argument("--out", type=pathlib.Path, default=pathlib.Path("."))

    p_del = sub.add_parser("del")
    p_del.add_argument("name")

    args = ap.parse_args()

    with socket.create_connection((args.host, args.port)) as sock:
        if args.cmd == "list":
