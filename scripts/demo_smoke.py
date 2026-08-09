"""Smoke P0 contra un FastAPI ya levantado, sin navegador ni credenciales."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE = os.getenv("DEMO_BASE_URL", "http://localhost:8000")


def request(method: str, path: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        BASE + path,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            return json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"{method} {path} -> {exc.code}: {detail}") from exc


def main() -> int:
    health = request("GET", "/api/health")
    assert health["status"] == "ok"
    ideas = request("GET", "/api/ideas/demo")
    idea = ideas[0]
    fixture = json.loads(
        (Path(__file__).parents[1] / "docs/demo/brief-mainframe.json").read_text()
    )
    project = request("POST", "/api/projects", {"raw_idea": idea["raw_idea"]})
    project_id = project["id"]
    request("POST", f"/api/projects/{project_id}/brief", fixture["brief"])
    run = request("POST", f"/api/projects/{project_id}/generate")
    if "--failure" in sys.argv:
        assert run["status"] == "GENERATION_FAILED"
        detail = request("GET", f"/api/projects/{project_id}")
        assert detail["brief"]["thesis"] == fixture["brief"]["thesis"]
        print(f"P0 failure smoke OK: project={project_id} status={run['status']}")
        return 0
    assert len(run["candidates"]) == 3
    evaluation = request("POST", f"/api/runs/{run['id']}/evaluate")
    candidate_id = evaluation["decision"]["best_candidate_id"]
    request("POST", f"/api/candidates/{candidate_id}/approve", {"reason": "Revisión editorial P0"})
    visual = request("POST", f"/api/candidates/{candidate_id}/visual")
    request("POST", f"/api/visuals/{visual['id']}/approve", {"reason": "Visual vinculado a la tesis"})
    receipt = request("POST", f"/api/candidates/{candidate_id}/publish-simulated")
    assert receipt["status"] == "SIMULATED_PUBLISHED"
    assert receipt["receipt"]["remote_id"] is None
    assert receipt["receipt"]["notice"] == "no se envió contenido a LinkedIn"
    print(f"P0 smoke OK: project={project_id} run={run['id']} status={receipt['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
