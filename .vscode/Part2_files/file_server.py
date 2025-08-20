#!/usr/bin/env python3
break
conn.sendall(chunk)


elif cmd == "DEL":
if len(parts) != 2:
send_line(conn, "ERR BAD_ARGS")
continue
try:
name = safe_name(parts[1])
except ValueError:
send_line(conn, "ERR BAD_NAME")
continue
target = root / name
if not target.exists():
send_line(conn, "ERR NOT_FOUND")
continue
with write_lock:
try:
os.remove(target)
send_line(conn, "OK")
except Exception:
send_line(conn, "ERR DELETE_FAILED")


elif cmd == "QUIT":
return
else:
send_line(conn, "ERR UNKNOWN_CMD")
except Exception:
# Keep server robust; log to stderr in a real system
try:
send_line(conn, "ERR SERVER_ERROR")
except Exception:
pass
finally:
try:
conn.close()
except Exception:
pass




def main():
ap = argparse.ArgumentParser(description="Simple file server")
ap.add_argument("--host", default="0.0.0.0")
ap.add_argument("--port", type=int, default=6001)
ap.add_argument("--root", default="./storage")
args = ap.parse_args()


root = pathlib.Path(args.root)
root.mkdir(parents=True, exist_ok=True)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((args.host, args.port))
server.listen()
print(f"File server listening on {args.host}:{args.port}, root={root.resolve()}")
while True:
conn, addr = server.accept()
threading.Thread(target=handle_client, args=(conn, addr, root), daemon=True).start()




if __name__ == "__main__":
main()