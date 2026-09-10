"""
StudyCrafter Web Application Server
Starts a local web server serving the modern StudyCrafter web app and opens the browser.
Usage:
    python run_web.py
"""

import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path

PORT = 3000
WEB_DIR = Path(__file__).resolve().parent / "web"


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_POST(self):
        # Local Agent & Webhook Endpoint
        if self.path in ("/api/agent", "/api/agent/", "/api/webhook", "/api/webhook/"):
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

            try:
                import json
                from backend.orchestrator import handle_turn
                from backend.state import StateManager

                payload = json.loads(post_body.decode("utf-8")) if post_body else {}
                student_id = payload.get("student_id") or "student_demo_01"
                message = payload.get("message", "")
                answer = payload.get("answer")
                topic = payload.get("topic")

                # If topic was explicitly chosen and student state has none or different
                if topic:
                    StateManager.update_profile(student_id, current_topic=topic)

                result = handle_turn(
                    student_id=student_id,
                    message=message or "",
                    answer=answer,
                )

                # Ensure agent_output format compatibility for web UI
                q = result.get("question")
                if q:
                    result["agent_output"] = {
                        "question": q.get("question"),
                        "options": [f"{k}) {v}" for k, v in q.get("options", {}).items()] if isinstance(q.get("options"), dict) else q.get("options", []),
                        "correct_answer": q.get("correct_answer"),
                        "difficulty": q.get("difficulty", "Medium"),
                        "topic": q.get("topic") or result.get("topic"),
                    }
                elif "evaluation" in result:
                    result["agent_output"] = result["evaluation"]

                resp_json = json.dumps(result).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_json)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp_json)
            except Exception as e:
                import json
                err_json = json.dumps({
                    "ok": False,
                    "action": "ERROR",
                    "response": f"⚠️ Agent Error: {str(e)}",
                    "error": str(e),
                }).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(err_json)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(err_json)
        else:
            self.send_error(404, "Endpoint not found")

    def end_headers(self):
        # Enable CORS and disable aggressive caching for development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, Authorization")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args):
        # Clean terminal logging
        sys.stderr.write(f"[StudyCrafter Web] {format % args}\n")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


def start_server():
    if not WEB_DIR.exists():
        print(f"Error: Directory {WEB_DIR} does not exist.")
        sys.exit(1)

    port = PORT
    max_attempts = 10

    for attempt in range(max_attempts):
        try:
            with ThreadedTCPServer(("", port), CustomHTTPRequestHandler) as httpd:
                url = f"http://localhost:{port}"
                print("=" * 60)
                print("[*] StudyCrafter AI Aptitude Tutor Web Application")
                print("=" * 60)
                print(f"[>] Serving from : {WEB_DIR}")
                print(f"[>] Local URL    : {url}")
                print(f"[>] n8n Backend  : https://nivi0706.app.n8n.cloud/webhook/studycrafter")
                print("=" * 60)
                print("Press Ctrl+C to stop the server.\n")

                try:
                    webbrowser.open(url)
                except Exception:
                    pass

                httpd.serve_forever()
                break
        except OSError as e:
            if "Address already in use" in str(e) or e.errno == 10048 or attempt < max_attempts - 1:
                port += 1
                continue
            else:
                raise e


if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n[StudyCrafter] Server stopped.")
        sys.exit(0)
