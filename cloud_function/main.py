"""
Cloud Function que actúa como webhook para disparar la pipeline
de actualización de dashboards LookML via GitHub Actions.

Se registra como Looker Action para que los usuarios puedan
activarla directamente desde el menú de cualquier dashboard.

Variables de entorno requeridas:
  GH_TOKEN          - GitHub PAT con permisos repo + workflow
  GH_REPO_OWNER     - Owner del repo (ej: sheila-gallardo-dvt)
  GH_REPO_NAME      - Nombre del repo (ej: base_project)
  ACTION_SECRET     - (Opcional) Secret compartido para validar requests de Looker
"""

import json
import os
import sys

import functions_framework
import requests


# --- Config ---
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO_OWNER = os.environ.get("GH_REPO_OWNER", "")
GH_REPO_NAME = os.environ.get("GH_REPO_NAME", "")
ACTION_SECRET = os.environ.get("ACTION_SECRET", "")

WORKFLOW_FILE = "update_dashboard.yml"


def trigger_github_workflow(dashboard_id: str) -> dict:
    """Dispara el workflow de GitHub Actions via la API."""
    url = (
        f"https://api.github.com/repos/{GH_REPO_OWNER}/{GH_REPO_NAME}"
        f"/actions/workflows/{WORKFLOW_FILE}/dispatches"
    )
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {GH_TOKEN}",
    }
    payload = {
        "ref": "main",
        "inputs": {"dashboard_id": str(dashboard_id)},
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=15)

    if resp.status_code == 204:
        return {"ok": True, "message": f"Workflow disparado para dashboard {dashboard_id}"}
    else:
        return {
            "ok": False,
            "message": f"Error {resp.status_code}: {resp.text}",
        }


def _get_base_url(request):
    """Construye la URL base HTTPS de esta Cloud Function."""
    # Usar X-Forwarded-Proto si está disponible (Cloud Run/Functions lo envía)
    proto = request.headers.get("X-Forwarded-Proto", "https")
    host = request.headers.get("Host", request.host)
    # Obtener la ruta raíz de la función (sin /form, /execute, etc.)
    path = request.path.rstrip("/")
    # Quitar subfijos conocidos para obtener la base
    for suffix in ("/form", "/execute", "/action_list"):
        if path.endswith(suffix):
            path = path[: -len(suffix)]
            break
    return f"{proto}://{host}{path}"


def _json_response(data, status=200):
    """Helper para devolver JSON con headers correctos."""
    return (
        json.dumps(data),
        status,
        {"Content-Type": "application/json"},
    )


# ──────────────────────────────────────────────
# Endpoint principal: Looker Action Hub
# ──────────────────────────────────────────────

@functions_framework.http
def looker_action(request):
    """
    Maneja los requests del Looker Action Hub.

    Looker puede enviar:
    - GET  (root)           → Action Hub listing
    - POST (root)           → Action Hub listing (algunos clientes)
    - POST .../form         → Formulario dinámico
    - POST .../execute      → Ejecución de la acción
    """
    path = request.path.rstrip("/")
    method = request.method

    # Log para debug
    print(f"[ACTION HUB] {method} {path}", file=sys.stderr)

    # Determinar qué endpoint se está llamando basado en el final del path
    is_form = path.endswith("/form")
    is_execute = path.endswith("/execute")
    is_root = not is_form and not is_execute

    # --- Action Hub listing (descubrimiento) ---
    if is_root:
        base_url = _get_base_url(request)
        return _json_response({
            "label": "LookML Dashboard Updater",
            "integrations": [
                {
                    "name": "update_lookml_dashboard",
                    "label": "🔄 Actualizar Dashboard en base_project",
                    "description": "Importa el LookML de este dashboard, limpia id/slug y reemplaza el modelo por @{model_name}",
                    "supported_action_types": ["dashboard"],
                    "icon_data_uri": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM1OGE2ZmYiIHN0cm9rZS13aWR0aD0iMiI+PHBhdGggZD0iTTIxIDE1djRhMiAyIDAgMCAxLTIgMkg1YTIgMiAwIDAgMS0yLTJ2LTQiLz48cG9seWxpbmUgcG9pbnRzPSIxNyA4IDEyIDMgNyA4Ii8+PGxpbmUgeDE9IjEyIiB5MT0iMyIgeDI9IjEyIiB5Mj0iMTUiLz48L3N2Zz4=",
                    "form_url": f"{base_url}/form",
                    "url": f"{base_url}/execute",
                    "supported_formats": ["txt"],
                    "params": [],
                }
            ],
        })

    # --- Formulario dinámico ---
    if is_form and method == "POST":
        return _json_response([
            {
                "name": "dashboard_id",
                "label": "Dashboard ID",
                "description": "ID del dashboard en Looker a actualizar en base_project",
                "type": "text",
                "required": True,
            },
            {
                "name": "confirm",
                "label": "Confirmar actualización",
                "description": "¿Seguro que quieres actualizar este dashboard?",
                "type": "select",
                "required": True,
                "options": [
                    {"name": "yes", "label": "✅ Sí, actualizar"},
                    {"name": "no", "label": "❌ No, cancelar"},
                ],
                "default": "yes",
            },
        ])

    # --- Ejecución de la acción ---
    if is_execute and method == "POST":
        try:
            body = request.get_json(silent=True) or {}
            form_params = body.get("form_params", {})
            dashboard_id = form_params.get("dashboard_id", "")
            confirm = form_params.get("confirm", "no")

            if confirm != "yes":
                return _json_response({
                    "looker": {"success": True, "message": "Acción cancelada por el usuario."}
                })

            if not dashboard_id:
                return _json_response({
                    "looker": {"success": False, "message": "Falta el Dashboard ID."}
                }, 400)

            # Validar secret si está configurado
            if ACTION_SECRET:
                auth_header = request.headers.get("Authorization", "")
                if f'Token token="{ACTION_SECRET}"' not in auth_header:
                    return _json_response({
                        "looker": {"success": False, "message": "Unauthorized"}
                    }, 401)

            result = trigger_github_workflow(dashboard_id)

            return _json_response({
                "looker": {"success": result["ok"], "message": result["message"]}
            })

        except Exception as e:
            print(f"[ACTION HUB] Error en execute: {e}", file=sys.stderr)
            return _json_response({
                "looker": {"success": False, "message": f"Error: {str(e)}"}
            }, 500)

    return _json_response({"error": "Not Found"}, 404)
