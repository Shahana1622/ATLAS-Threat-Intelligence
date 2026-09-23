from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from backend.threat_platform.services.investigator import (build_coverage_validation, build_dashboard,
                                                   build_graph, build_report, build_timeline,
                                                   cas_explanation, export_csv, export_json,
                                                   export_pdf, investigate_actor)
from backend.threat_platform.services.pipeline import run_analysis
from backend.threat_platform.services.storage import dataset_path, load_dataset


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path.startswith("/ui/") or parsed.path == "/":
            self._send_ui(parsed.path)
            return
        dataset = load_dataset(dataset_path())
        analyses = run_analysis(dataset)
        if parsed.path == "/health":
            payload = {"status": "ok", "data_origin": "synthetic"}
            self._send(payload)
        elif parsed.path == "/dataset":
            self._send(dataset)
        elif parsed.path == "/v1/investigator/dashboard":
            self._send(build_dashboard(dataset, analyses))
        elif parsed.path == "/v1/analysis":
            self._send(analyses)
        elif parsed.path == "/v1/investigator/graph":
            self._send(build_graph(dataset))
        elif parsed.path == "/v1/investigator/timeline":
            self._send(build_timeline(dataset, query.get("actor_id", [None])[0],
                                      query.get("start", [None])[0], query.get("end", [None])[0]))
        elif parsed.path == "/v1/investigator/cas":
            self._send(cas_explanation(dataset, query.get("actor_id", [None])[0], analyses))
        elif parsed.path == "/v1/investigator/coverage":
            self._send(build_coverage_validation())
        elif parsed.path.startswith("/v1/investigator/actors/"):
            self._send(investigate_actor(dataset, parsed.path.rsplit("/", 1)[-1]))
        elif parsed.path == "/v1/investigator/report":
            self._send(build_report(dataset, query.get("actor_id", [None])[0], analyses))
        elif parsed.path == "/v1/investigator/export.json":
            self._download(export_json(build_report(dataset, query.get("actor_id", [None])[0], analyses)), "report.json", "application/json")
        elif parsed.path == "/v1/investigator/export.csv":
            self._download(export_csv(build_report(dataset, query.get("actor_id", [None])[0], analyses)), "report.csv", "text/csv")
        elif parsed.path == "/v1/investigator/export.pdf":
            self._download(export_pdf(build_report(dataset, query.get("actor_id", [None])[0], analyses)), "report.pdf", "application/pdf")
        else:
            self.send_error(404, "Not found")

    def _send(self, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _download(self, body: bytes, filename: str, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_ui(self, path: str) -> None:
        filename = "index.html" if path == "/" else path.removeprefix("/ui/")
        root = Path(__file__).resolve().parents[1] / "ui"
        requested = (root / filename).resolve()
        if root not in requested.parents or not requested.is_file():
            self.send_error(404, "Not found")
            return
        body = requested.read_bytes()
        content_type = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}.get(requested.suffix, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    from backend.threat_platform.services.generator import generate_dataset
    from backend.threat_platform.services.storage import save_dataset
    save_dataset(generate_dataset(), dataset_path())
    server = HTTPServer(("127.0.0.1", 8765), Handler)
    print("Local synthetic API listening at http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()

