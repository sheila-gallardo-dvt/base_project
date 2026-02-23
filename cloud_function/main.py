"""
Cloud Function que actúa como webhook para disparar la pipeline
de actualización de dashboards LookML via GitHub Actions.

Se registra como Looker Action para que los usuarios puedan
activarla directamente desde el menú de cualquier dashboard.

Variables de entorno requeridas:
  GH_TOKEN          - GitHub PAT con permisos repo + workflow
  GH_REPO_OWNER     - Owner del repo (ej: sheila-gallardo-dvt)
  GH_REPO_NAME      - Nombre del repo (ej: base_project)
  FUNCTION_URL      - URL pública de esta Cloud Function
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
FUNCTION_URL = os.environ.get("FUNCTION_URL", "").rstrip("/")

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


def _json_response(data, status=200):
    """Helper para devolver JSON con headers correctos."""
    return (
        json.dumps(data),
        status,
        {"Content-Type": "application/json"},
    )


def _action_list():
    """Devuelve el listado de acciones disponibles (descubrimiento)."""
    return _json_response({
        "label": "LookML Dashboard Updater",
        "integrations": [
            {
                "name": "update_lookml_dashboard",
                "label": "🔄 Actualizar Dashboard en base_project",
                "description": "Importa el LookML de este dashboard, limpia id/slug y reemplaza el modelo por @{model_name}",
                "supported_action_types": ["dashboard"],
                "icon_data_uri": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM1OGE2ZmYiIHN0cm9rZS13aWR0aD0iMiI+PHBhdGggZD0iTTIxIDE1djRhMiAyIDAgMCAxLTIgMkg1YTIgMiAwIDAgMS0yLTJ2LTQiLz48cG9seWxpbmUgcG9pbnRzPSIxNyA4IDEyIDMgNyA4Ii8+PGxpbmUgeDE9IjEyIiB5MT0iMyIgeDI9IjEyIiB5Mj0iMTUiLz48L3N2Zz4=",
                "form_url": f"{FUNCTION_URL}/form",
                "url": f"{FUNCTION_URL}/execute",
                "supported_formats": ["txt"],
                "params": [],
            }
        ],
    })


def _action_form():
    """Devuelve el formulario dinámico de la acción."""
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


def _action_execute(body):
    """Ejecuta la acción: dispara el workflow de GitHub Actions."""
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

    result = trigger_github_workflow(dashboard_id)

    return _json_response({
        "looker": {"success": result["ok"], "message": result["message"]}
    })


# ──────────────────────────────────────────────
# Endpoint principal
# ──────────────────────────────────────────────

@functions_framework.http
def looker_action(request):
    """
    Endpoint único que maneja todos los requests del Looker Action Hub.
    
    Cloud Functions no soporta sub-paths, así que detectamos el tipo
    de request por el MÉTODO + CONTENIDO DEL BODY:
    
    - GET  → Descubrimiento (action list)
    - POST sin body / sin form_params → Formulario (form)
    - POST con form_params → Ejecución (execute)
    """
    method = request.method
    body = request.get_json(silent=True) or {}

    print(f"[ACTION HUB] {method} | body keys: {list(body.keys())}", file=sys.stderr)

    try:
        # GET → Descubrimiento
        if method == "GET":
            return _action_list()

        # POST → Distinguir entre test, form y execute por el contenido
        if method == "POST":
            # Si tiene form_params → es una ejecución
            if "form_params" in body:
                print(f"[ACTION HUB] EXECUTE: form_params={body['form_params']}", file=sys.stderr)
                return _action_execute(body)

            # Si tiene data/scheduled_plan → Looker pide el formulario
            if "data" in body or "scheduled_plan" in body:
                print("[ACTION HUB] FORM request", file=sys.stderr)
                return _action_form()

            # Body vacío → Test de conectividad de Looker
            print("[ACTION HUB] TEST (empty body) → OK", file=sys.stderr)
            return _json_response({
                "looker": {"success": True, "message": "Action Hub conectado correctamente."}
            })

        return _json_response({"error": "Method not allowed"}, 405)

    except Exception as e:
        print(f"[ACTION HUB] ERROR: {e}", file=sys.stderr)
        return _json_response({
            "looker": {"success": False, "message": f"Error: {str(e)}"}
        }, 500)
