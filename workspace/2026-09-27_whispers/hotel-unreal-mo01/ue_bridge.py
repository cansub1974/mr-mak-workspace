"""Stdio client for the ue-mcp bridge (Whispers 5.8). Unlike the editor's native MCP execute_python_code, the bridge's
run_python_file does not save dirty packages before it runs, so other sessions' unsaved work is never written.

    python ue_bridge.py tools                          # tool names
    python ue_bridge.py run <script.py> [arg ...]      # editor/run_python_file, as __main__ with sys.argv = [script, args...]
    python ue_bridge.py call <tool> '<json args>'      # any tool call

Lesson from EC01: `cmd /c ue-mcp <uproject>` starts the node server as a grandchild. Close stdin, then end the whole tree
(taskkill /T) in a finally, so no server is leaked even when a call times out.
"""
import json, os, subprocess, sys, threading, time

UPROJECT = "D:/Unreal Projects/Whispers 5.8/Whispers.uproject"


class Bridge:
    def __init__(self):
        self.p = subprocess.Popen(["cmd", "/c", "ue-mcp", UPROJECT], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, bufsize=0)
        self.rid = 0
        self.lines = []
        self.err = []
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._read_err, daemon=True).start()

    def _read(self):
        for raw in iter(self.p.stdout.readline, b""):
            self.lines.append(raw.decode("utf-8", "replace"))

    def _read_err(self):
        for raw in iter(self.p.stderr.readline, b""):
            self.err.append(raw.decode("utf-8", "replace"))

    def send(self, method, params=None, notify=False):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            self.rid += 1
            msg["id"] = self.rid
        self.p.stdin.write((json.dumps(msg) + "\n").encode()); self.p.stdin.flush()
        return None if notify else self.rid

    def wait(self, rid, timeout):
        t0 = time.time()
        while time.time() - t0 < timeout:
            for i, ln in enumerate(self.lines):
                try:
                    m = json.loads(ln)
                except Exception:
                    continue
                if m.get("id") == rid:
                    del self.lines[i]
                    return m
            if self.p.poll() is not None:
                raise RuntimeError("ue-mcp exited: " + "".join(self.err[-20:]))
            time.sleep(0.05)
        raise TimeoutError(f"no reply to {rid} in {timeout}s")

    def request(self, method, params=None, timeout=120):
        return self.wait(self.send(method, params), timeout)

    def start(self):
        r = self.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                        "clientInfo": {"name": "mo01-port", "version": "1"}}, timeout=180)
        self.send("notifications/initialized", {}, notify=True)
        return r

    def close(self):
        try:
            self.p.stdin.close()
        except Exception:
            pass
        for _ in range(30):
            if self.p.poll() is not None:
                break
            time.sleep(0.1)
        if self.p.poll() is None:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(self.p.pid)], capture_output=True)


def text(res):
    if "error" in res:
        return "ERROR " + json.dumps(res["error"])
    out = [c.get("text", json.dumps(c)) for c in res.get("result", {}).get("content", [])]
    if res.get("result", {}).get("isError"):
        out.insert(0, "TOOL ERROR")
    return "\n".join(out)


def call(tool, args, timeout=1800):
    b = Bridge()
    try:
        b.start()
        return b.request("tools/call", {"name": tool, "arguments": args}, timeout=timeout)
    finally:
        b.close()


def run_file(path, args=(), timeout=1800):
    """editor.run_python_file through the bridge's one meta-tool ("tools", action "call")."""
    return call("tools", {"action": "call", "category": "editor", "method": "run_python_file",
                          "args": {"filePath": os.path.abspath(path).replace("\\", "/"), "asMain": True, "args": list(args),
                                   "maxLogChars": 60000, "timeoutMs": int(timeout * 1000)}}, timeout + 60)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1]
    if cmd == "tools":
        b = Bridge()
        try:
            b.start()
            r = b.request("tools/list", {})
            for t in r["result"]["tools"]:
                print(t["name"], "::", (t.get("description") or "")[:160].replace("\n", " "))
        finally:
            b.close()
    elif cmd == "run":
        print(text(run_file(sys.argv[2], sys.argv[3:])))
    elif cmd == "call":
        print(text(call(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})))
