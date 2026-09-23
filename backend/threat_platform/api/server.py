from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from threat_platform.services.investigator import (
    build_coverage_validation,
    build_dashboard,
    build_graph,
    build_report,
    build_timeline,
    cas_explanation,
    export_csv,
    export_json,
    export_pdf,
    investigate_actor,
)
from threat_platform.services.pipeline import run_analysis
from threat_platform.services.storage import dataset_path, load_dataset


# Frontend URL.
# For local testing, "*" allows all origins.
# In Render, you can set FRONTEND_URL to your actual frontend URL.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")


class Handler(BaseHTTPRequestHandler):

    def _add_cors_headers(self):
        self.send_header(
            "Access-Control-Allow-Origin",
            FRONTEND_URL
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, OPTIONS"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

    def do_OPTIONS(self):
        self.send_response(204)
        self._add_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        # Health check
        if parsed.path == "/health":
            self._send({
                "status": "ok",
                "data_origin": "synthetic"
            })
            return

        # Load data
        dataset = load_dataset(dataset_path())
        analyses = run_analysis(dataset)

        if parsed.path == "/dataset":
            self._send(dataset)

        elif parsed.path == "/v1/investigator/dashboard":
            self._send(
                build_dashboard(dataset, analyses)
            )

        elif parsed.path == "/v1/analysis":
            self._send(analyses)

        elif parsed.path == "/v1/investigator/graph":
            self._send(
                build_graph(dataset)
            )

        elif parsed.path == "/v1/investigator/timeline":
            actor_id = query.get("actor_id", [None])[0]
            start = query.get("start", [None])[0]
            end = query.get("end", [None])[0]

            self._send(
                build_timeline(
                    dataset,
                    actor_id,
                    start,
                    end
                )
            )

        elif parsed.path == "/v1/investigator/cas":
            actor_id = query.get("actor_id", [None])[0]

            self._send(
                cas_explanation(
                    dataset,
                    actor_id,
                    analyses
                )
            )

        elif parsed.path == "/v1/investigator/coverage":
            self._send(
                build_coverage_validation()
            )

        elif parsed.path.startswith("/v1/investigator/actors/"):
            actor_id = parsed.path.rsplit("/", 1)[-1]

            self._send(
                investigate_actor(
                    dataset,
                    actor_id
                )
            )

        elif parsed.path == "/v1/investigator/report":
            actor_id = query.get("actor_id", [None])[0]

            self._send(
                build_report(
                    dataset,
                    actor_id,
                    analyses
                )
            )

        elif parsed.path == "/v1/investigator/export.json":
            actor_id = query.get("actor_id", [None])[0]

            report = build_report(
                dataset,
                actor_id,
                analyses
            )

            self._download(
                export_json(report),
                "report.json",
                "application/json"
            )

        elif parsed.path == "/v1/investigator/export.csv":
            actor_id = query.get("actor_id", [None])[0]

            report = build_report(
                dataset,
                actor_id,
                analyses
            )

            self._download(
                export_csv(report),
                "report.csv",
                "text/csv"
            )

        elif parsed.path == "/v1/investigator/export.pdf":
            actor_id = query.get("actor_id", [None])[0]

            report = build_report(
                dataset,
                actor_id,
                analyses
            )

            self._download(
                export_pdf(report),
                "report.pdf",
                "application/pdf"
            )

        else:
            self.send_error(404, "Not found")

    def _send(self, payload):
        body = json.dumps(
            payload,
            indent=2,
            default=str
        ).encode("utf-8")

        self.send_response(200)

        self._add_cors_headers()

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)

    def _download(self, body, filename, content_type):
        self.send_response(200)

        self._add_cors_headers()

        self.send_header(
            "Content-Type",
            content_type
        )

        self.send_header(
            "Content-Disposition",
            f'attachment; filename="{filename}"'
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)

    def log_message(self, format, *args):
        # Disable default HTTP logging
        return


def main():
    # Generate the synthetic dataset
    from threat_platform.services.generator import generate_dataset
    from threat_platform.services.storage import save_dataset

    save_dataset(
        generate_dataset(),
        dataset_path()
    )

    # Render provides PORT automatically.
    # Local development uses 8765.
    port = int(
        os.environ.get("PORT", "8765")
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        Handler
    )

    print(
        f"Threat Intelligence API running on port {port}"
    )

    server.serve_forever()


if __name__ == "__main__":
    main()