#!/usr/bin/env python3
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


p_list = sub.add_parser("list")


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
exit(do_list(sock))
elif args.cmd == "put":
if not args.path.exists():
print("Path does not exist")
exit(1)
exit(do_put(sock, args.path))
elif args.cmd == "get":
args.out.mkdir(parents=True, exist_ok=True)
exit(do_get(sock, args.name, args.out))
elif args.cmd == "del":
exit(do_del(sock, args.name))




if __name__ == "__main__":
main()