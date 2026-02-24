#!/usr/bin/env python3
"""
Pipeline para actualizar dashboards LookML de un proyecto tenant.

Dos escenarios:
1. Dashboard NUEVO (no extiende base) → genera fichero completo
2. Dashboard que EXTIENDE el base → compara con la versión base al ref
   pinned del tenant y genera un extends con solo los elementos nuevos/modificados.

Uso:
  python update_tenant_dashboard.py \
    --dashboard_id 270 \
    --tenant_name tenant_1 \
    --tenant_dir ../tenant_1 \
    --base_repo_owner sheila-gallardo-dvt \
    --base_repo_name base_project
"""

import argparse
import os
import re
import sys
import textwrap

import looker_sdk
import requests
import yaml


# ──────────────────────────────────────────────
# 1. Looker API
# ──────────────────────────────────────────────

def get_dashboard_lookml(sdk, dashboard_id: str) -> str:
    """Obtiene el LookML de un dashboard desde la API de Looker."""
    try:
        result = sdk.dashboard_lookml(dashboard_id)
        if not result.lookml:
            print(f"ERROR: El dashboard '{dashboard_id}' no devolvió LookML.")
            sys.exit(1)
        return result.lookml
    except Exception as e:
        print(f"ERROR al obtener el dashboard '{dashboard_id}': {e}")
        sys.exit(1)


# ──────────────────────────────────────────────
# 2. Parseo del manifest del tenant
# ──────────────────────────────────────────────

def parse_tenant_manifest(manifest_path: str) -> dict:
    """
    Lee el manifest.lkml del tenant y extrae:
    - base_repo_url: URL del repo base
    - base_ref: ref (tag/commit) del base
    - model_name: valor del override_constant model_name
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read()

    info = {}

    # URL del repo base
    url_match = re.search(r'url:\s*"([^"]+)"', content)
    if url_match:
        info["base_repo_url"] = url_match.group(1)
        # Extraer owner/repo del URL
        gh_match = re.search(r"github\.com/([^/]+)/([^/.]+)", info["base_repo_url"])
        if gh_match:
            info["base_owner"] = gh_match.group(1)
            info["base_repo"] = gh_match.group(2)

    # Ref del base
    ref_match = re.search(r'ref:\s*"([^"]+)"', content)
    if ref_match:
        info["base_ref"] = ref_match.group(1)

    # Model name del tenant
    model_match = re.search(
        r'override_constant:\s*model_name\s*\{[^}]*value:\s*"([^"]+)"',
        content,
        re.DOTALL,
    )
    if model_match:
        info["model_name"] = model_match.group(1)

    return info


# ──────────────────────────────────────────────
# 3. GitHub API: obtener fichero base al ref
# ──────────────────────────────────────────────

def get_base_dashboard_from_github(
    owner: str, repo: str, ref: str, dashboard_name: str, gh_token: str
) -> str | None:
    """
    Obtiene el contenido del dashboard del base_project en GitHub
    al ref específico (tag o commit) del tenant.
    """
    # Buscar en dashboards/ del repo base
    path = f"dashboards/{dashboard_name}.dashboard.lookml"
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "Authorization": f"Bearer {gh_token}",
    }

    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code == 200:
        return resp.text
    elif resp.status_code == 404:
        print(f"  ℹ️  Dashboard '{dashboard_name}' no encontrado en base_project@{ref}")
        return None
    else:
        print(f"  ⚠️  Error {resp.status_code} al obtener base dashboard: {resp.text}")
        return None


# ──────────────────────────────────────────────
# 4. Parseo y comparación de dashboards
# ──────────────────────────────────────────────

def parse_dashboard_yaml(lookml: str) -> dict:
    """Parsea el LookML de un dashboard como YAML."""
    docs = yaml.safe_load(lookml)
    if isinstance(docs, list) and len(docs) > 0:
        return docs[0]
    return docs or {}


class LookMLDumper(yaml.SafeDumper):
    """Dumper YAML personalizado para LookML."""
    pass

class FlowList(list):
    """Lista que se pintará en estilo flow [a, b]."""
    pass

class FlowDict(dict):
    """Diccionario que se pintará en estilo flow {a: b}."""
    pass

def represent_flow_list(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

def represent_flow_dict(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data, flow_style=True)

# Registrar tipos para que se pinten en estilo flow
LookMLDumper.add_representer(FlowList, represent_flow_list)
LookMLDumper.add_representer(FlowDict, represent_flow_dict)

def wrap_flow_structures(data):
    """
    Recorre los datos y envuelve listas/dicts específicos en FlowList/FlowDict
    para que el dumper los pinte en una sola línea.
    """
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # Estos campos suelen ir en una sola línea en LookML
            if k in ["extends", "fields", "sorts", "listens_to_filters", "listen"]:
                if isinstance(v, list):
                    new_dict[k] = FlowList(v)
                elif isinstance(v, dict):
                    # Solo convertir a FlowDict si no es muy grande (opcional)
                    new_dict[k] = FlowDict(v)
                else:
                    new_dict[k] = v
            else:
                new_dict[k] = wrap_flow_structures(v)
        return new_dict
    elif isinstance(data, list):
        return [wrap_flow_structures(item) for item in data]
    return data

def normalize_element(element: dict, remove_model: bool = False) -> dict:
    """Normaliza un elemento para comparación (quita campos volátiles y ruidosos)."""
    normalized = dict(element)
    
    # 1. Quitar identificadores volátiles de la API
    for key in ("id", "slug", "preferred_slug"):
        normalized.pop(key, None)
    
    # 2. Quitar el modelo si se solicita (para comparar lógica pura)
    if remove_model:
        normalized.pop("model", None)
    
    # 3. Quitar campos por defecto ruidosos que Looker API añade pero no suelen estar en el .lookml base
    noisy_defaults = {
        "show_view_names": False,
        "show_comparison": False,
        "comparison_type": "value",
        "comparison_reverse_colors": False,
        "show_comparison_label": True,
        "enable_conditional_formatting": False,
        "conditional_formatting_include_totals": False,
        "conditional_formatting_include_nulls": False,
        "defaults_version": 1,
        "tab_name": "",
        "hidden": False,
        "transpose": False,
        "truncate_text": True,
        "hide_totals": False,
        "hide_row_totals": False,
        "size_to_fit": True,
        "row": None, # Las filas/cols a veces cambian si no están fijas
        "col": None,
        "width": None,
        "height": None,
    }
    
    # Solo quitar si el valor coincide con el default ruidoso
    # Esto evita "falsos positivos" de cambio
    for key, default_val in noisy_defaults.items():
        if key in normalized and normalized[key] == default_val:
            normalized.pop(key)
            
    return normalized


def compare_elements(tenant_elements: list, base_elements: list) -> list:
    """
    Compara los elementos del tenant con los del base.
    Devuelve solo los elementos NUEVOS o MODIFICADOS.
    """
    # Indexar base elements por name
    base_by_name = {}
    for el in base_elements:
        name = el.get("name", "")
        if name:
            base_by_name[name] = el

    diff_elements = []
    for tenant_el in tenant_elements:
        name = tenant_el.get("name", "")

        # Normalizar para comparación (quitar model y campos volátiles)
        tenant_norm = normalize_element(tenant_el, remove_model=True)
        
        if name not in base_by_name:
            # Elemento NUEVO (no existe en base) → incluir
            diff_elements.append(tenant_el)
        else:
            # Existe en base → comprobar si ha sido modificado
            base_norm = normalize_element(base_by_name[name], remove_model=True)
            if tenant_norm != base_norm:
                # MODIFICADO → incluir
                diff_elements.append(tenant_el)
            # Si son iguales → heredado, no incluir

    return diff_elements


def compare_filters(tenant_filters: list, base_filters: list) -> list:
    """Compara filtros del tenant con los del base. Devuelve nuevos/modificados."""
    base_by_name = {f.get("name", ""): f for f in base_filters}

    diff_filters = []
    for tenant_f in tenant_filters:
        name = tenant_f.get("name", "")
        tenant_norm = normalize_element(tenant_f, remove_model=True)

        if name not in base_by_name:
            diff_filters.append(tenant_f)
        else:
            base_norm = normalize_element(base_by_name[name], remove_model=True)
            if tenant_norm != base_norm:
                diff_filters.append(tenant_f)

    return diff_filters


# ──────────────────────────────────────────────
# 5. Generación del LookML de salida
# ──────────────────────────────────────────────

def clean_lookml(lookml: str) -> str:
    """Limpia el LookML: quita id, slug, preferred_slug."""
    lines = lookml.split("\n")
    filtered = []
    for line in lines:
        if re.match(r"^\s{2,4}(id|slug|preferred_slug)\s*:", line):
            continue
        filtered.append(line)
    return "\n".join(filtered)


def replace_model_name(lookml: str, target_model: str = "@{model_name}") -> str:
    """Reemplaza el nombre del modelo por el target_model."""
    # Asegurar que el target_model tiene comillas si no es la variable @{}
    if not target_model.startswith("@{"):
        replacement = f'"{target_model}"'
    else:
        replacement = target_model

    # Esta regex es más robusta:
    # Captura 'model: "...", 'model: ...', o 'model: @{...}'
    # El valor a reemplazar puede estar entre comillas, ser un simple string o una constante @{}
    lookml = re.sub(r'(model:\s*)(?:\"[^\"]*\"|[@\w{}]+)', rf'\1{replacement}', lookml)
    return lookml


def generate_extends_dashboard(
    dashboard_name: str,
    tenant_name: str,
    base_dashboard_name: str,
    diff_elements: list,
    diff_filters: list,
    tenant_title: str = "",
    tenant_model: str = "",
) -> str:
    """
    Genera el LookML de un dashboard que extiende el base,
    incluyendo solo los elementos nuevos/modificados.
    """
    dashboard = {
        "dashboard": f"{dashboard_name}",
        "title": tenant_title or f"{base_dashboard_name} - {tenant_name}",
        "extends": [base_dashboard_name],
    }

    if diff_elements:
        dashboard["elements"] = diff_elements

    if diff_filters:
        dashboard["filters"] = diff_filters

    # Envolver estructuras que queremos en estilo flow [a, b] o {a: b}
    dashboard_wrapped = wrap_flow_structures(dashboard)

    # Generar YAML
    output = yaml.dump(
        [dashboard_wrapped],
        Dumper=LookMLDumper,
        default_flow_style=False,  # Asegura estilo bloque por defecto
        allow_unicode=True,
        sort_keys=False,
        width=200,
    )

    # Asegurar el separador YAML al inicio
    if not output.startswith("---\n"):
        output = "---\n" + output

    # Reemplazar modelo por el nombre real del tenant si se proporciona
    if tenant_model:
        output = replace_model_name(output, tenant_model)
    else:
        output = replace_model_name(output)
    
    return output


def generate_standalone_dashboard(lookml: str, tenant_model: str = "") -> str:
    """Genera un dashboard standalone (sin extend): limpia y reemplaza modelo."""
    # Para standalone, el LookML ya viene generado (formato Looker API).
    # Pero si lo queremos exacto al formato del base project (flow style), 
    # tendríamos que parsearlo y re-generarlo.
    parsed = parse_dashboard_yaml(lookml)
    if not parsed:
        return lookml
        
    dashboard_wrapped = wrap_flow_structures(parsed)
    output = yaml.dump(
        [dashboard_wrapped],
        Dumper=LookMLDumper,
        default_flow_style=False,  # Asegura estilo bloque por defecto
        allow_unicode=True,
        sort_keys=False,
        width=200,
    )
    
    if not output.startswith("---\n"):
        output = "---\n" + output
        
    if tenant_model:
        output = replace_model_name(output, tenant_model)
    else:
        output = replace_model_name(output)
        
    return output


# ──────────────────────────────────────────────
# 6. Fichero de salida
# ──────────────────────────────────────────────

def find_existing_file(dashboards_dir: str, dashboard_name: str) -> str | None:
    """Busca si ya existe un fichero para el dashboard."""
    exact_path = os.path.join(dashboards_dir, f"{dashboard_name}.dashboard.lookml")
    if os.path.exists(exact_path):
        return exact_path

    if os.path.isdir(dashboards_dir):
        for filename in os.listdir(dashboards_dir):
            if not filename.endswith(".dashboard.lookml"):
                continue
            filepath = os.path.join(dashboards_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                if re.search(
                    rf"^-?\s*dashboard:\s+{re.escape(dashboard_name)}\s*$",
                    content,
                    re.MULTILINE,
                ):
                    return filepath
            except Exception:
                continue
    return None


def detect_base_dashboard_name(tenant_dashboards_dir: str, dashboard_name: str) -> str | None:
    """
    Si ya hay un fichero para este dashboard en el tenant,
    lee el extends para saber cuál es el base dashboard.
    """
    existing = find_existing_file(tenant_dashboards_dir, dashboard_name)
    if not existing:
        return None
    
    with open(existing, "r", encoding="utf-8") as f:
        content = f.read()

    # Intentar detectar estilo flow: extends: [name]
    match = re.search(r"extends:\s*\[(\w+)\]", content)
    if match:
        return match.group(1)
    
    # Intentar detectar estilo block:
    # extends:
    # - name
    match = re.search(r"extends:\s*\n\s+-\s+(\w+)", content)
    if match:
        return match.group(1)
    
    return None


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Actualiza dashboards LookML de un tenant con diff frente al base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dashboard_id", required=True, help="ID del dashboard en Looker")
    parser.add_argument("--tenant_name", required=True, help="Nombre del tenant (ej: tenant_1)")
    parser.add_argument("--tenant_dir", default=None, help="Ruta al proyecto del tenant")
    parser.add_argument("--base_dashboard", default=None,
                        help="Nombre del dashboard base que extiende (si aplica). Si no se indica, se intenta detectar automáticamente.")
    parser.add_argument("--base_repo_owner", default=None,
                        help="Owner del repo base en GitHub (override del manifest)")
    parser.add_argument("--base_repo_name", default=None,
                        help="Nombre del repo base en GitHub (override del manifest)")
    parser.add_argument("--dry_run", action="store_true", help="Muestra resultado sin guardar")

    args = parser.parse_args()

    # Resolver directorio del tenant
    if args.tenant_dir:
        tenant_dir = os.path.abspath(args.tenant_dir)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        tenant_dir = os.path.join(script_dir, "..", "..", args.tenant_name)
    tenant_dir = os.path.abspath(tenant_dir)

    dashboards_dir = os.path.join(tenant_dir, "dashboards")
    manifest_path = os.path.join(tenant_dir, "manifest.lkml")

    print(f"📁 Tenant dir: {tenant_dir}")

    # --- Paso 1: Obtener LookML del dashboard ---
    print("📡 Conectando con Looker API...")
    sdk = looker_sdk.init40()

    print(f"📥 Obteniendo LookML del dashboard ID: {args.dashboard_id}")
    raw_lookml = get_dashboard_lookml(sdk, args.dashboard_id)

    # Extraer nombre del dashboard
    name_match = re.search(r"^-\s+dashboard:\s+(\S+)", raw_lookml, re.MULTILINE)
    if not name_match:
        print("ERROR: No se pudo detectar el nombre del dashboard.")
        sys.exit(1)
    dashboard_name = name_match.group(1)
    print(f"📋 Dashboard detectado: '{dashboard_name}'")

    # --- Paso 2: Determinar si es un extend ---
    # Primero: ¿se indicó explícitamente un base_dashboard?
    base_dashboard_name = args.base_dashboard

    # Si no, intentar detectar del fichero existente
    if not base_dashboard_name:
        base_dashboard_name = detect_base_dashboard_name(dashboards_dir, dashboard_name)

    # Obtener info básica del tenant (model name) siempre
    tenant_model = args.tenant_name
    base_ref = "main"
    base_owner = args.base_repo_owner or ""
    base_repo = args.base_repo_name or ""

    if os.path.exists(manifest_path):
        print(f"📄 Leyendo manifest: {manifest_path}")
        manifest_info = parse_tenant_manifest(manifest_path)
        tenant_model = manifest_info.get("model_name", tenant_model)
        base_ref = manifest_info.get("base_ref", base_ref)
        if not base_owner:
            base_owner = manifest_info.get("base_owner", "")
        if not base_repo:
            base_repo = manifest_info.get("base_repo", "")

    gh_token = os.environ.get("GH_TOKEN", "")

    if base_dashboard_name:
        # ─── CASO EXTEND ───
        print(f"🔗 Dashboard extiende: '{base_dashboard_name}'")
        print(f"  📌 Base ref: {base_ref}")
        print(f"  📦 Base repo: {base_owner}/{base_repo}")
        print(f"  🏗️  Tenant model: {tenant_model}")

        # Obtener base dashboard desde GitHub
        print(f"📥 Obteniendo base dashboard '{base_dashboard_name}' @ {base_ref}...")
        base_lookml = get_base_dashboard_from_github(
            base_owner, base_repo, base_ref, base_dashboard_name, gh_token
        )

        if not base_lookml:
            print("⚠️  No se encontró el base dashboard. Generando como standalone.")
            output = generate_standalone_dashboard(raw_lookml)
        else:
            # Parsear ambos dashboards
            tenant_parsed = parse_dashboard_yaml(raw_lookml)
            base_parsed = parse_dashboard_yaml(base_lookml)

            tenant_elements = tenant_parsed.get("elements", [])
            base_elements = base_parsed.get("elements", [])
            tenant_filters = tenant_parsed.get("filters", [])
            base_filters = base_parsed.get("filters", [])

            # Comparar
            diff_elements = compare_elements(tenant_elements, base_elements)
            diff_filters = compare_filters(tenant_filters, base_filters)

            n_new = len(diff_elements)
            n_base = len(base_elements)
            n_total = len(tenant_elements)
            print(f"  📊 Elementos: {n_total} total, {n_base} base, {n_new} nuevos/modificados")
            print(f"  📊 Filtros diff: {len(diff_filters)}")

            # Título del tenant
            tenant_title = tenant_parsed.get("title", "")

            output = generate_extends_dashboard(
                dashboard_name=dashboard_name,
                tenant_name=args.tenant_name,
                base_dashboard_name=base_dashboard_name,
                diff_elements=diff_elements,
                diff_filters=diff_filters,
                tenant_title=tenant_title,
                tenant_model=tenant_model,
            )
    else:
        # ─── CASO NUEVO (sin extend) ───
        print(f"🆕 Dashboard nuevo (sin extend del base). Model: {tenant_model}")
        output = generate_standalone_dashboard(raw_lookml, tenant_model=tenant_model)

    # --- Paso 3: Guardar ---
    existing = find_existing_file(dashboards_dir, dashboard_name)
    if existing:
        filepath = existing
        action = "ACTUALIZADO"
    else:
        filepath = os.path.join(dashboards_dir, f"{dashboard_name}.dashboard.lookml")
        action = "CREADO"

    if args.dry_run:
        print(f"\n--- DRY RUN: {action} → {filepath} ---")
        print(output)
    else:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n✅ Dashboard {action}: {filepath}")

    # GitHub Actions outputs
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"dashboard_name={dashboard_name}\n")
            f.write(f"file_path={filepath}\n")
            f.write(f"action={action}\n")
            f.write(f"is_extend={'true' if base_dashboard_name else 'false'}\n")


if __name__ == "__main__":
    main()
