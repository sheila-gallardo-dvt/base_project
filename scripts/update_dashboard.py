#!/usr/bin/env python3
"""
Pipeline para actualizar dashboards LookML del base_project.

Obtiene el LookML de un dashboard de Looker via API, lo limpia
(quita id/slug, reemplaza modelo por @{model_name}) y lo guarda
en base_project/dashboards/.
"""

import argparse
import os
import re
import sys
import textwrap

import looker_sdk
from looker_sdk import models40 as models


def get_dashboard_lookml(sdk: looker_sdk.methods40.Looker40SDK, dashboard_id: str) -> str:
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


def extract_dashboard_name(lookml: str) -> str:
    """
    Extrae el nombre del dashboard del código LookML.
    Busca la línea '- dashboard: <nombre>' en el YAML.
    """
    match = re.search(r"^-\s+dashboard:\s+(\S+)", lookml, re.MULTILINE)
    if not match:
        print("ERROR: No se pudo detectar el nombre del dashboard en el LookML.")
        sys.exit(1)
    return match.group(1)


def remove_id_and_slug(lookml: str) -> str:
    """
    Elimina las líneas de 'id:', 'slug:' y 'preferred_slug:' del dashboard LookML.
    Esto permite que Looker mantenga los valores previos al importar.
    
    Solo elimina id/slug/preferred_slug a nivel de dashboard (indentación de 2 espacios),
    no dentro de los elements u otros bloques anidados.
    """
    lines = lookml.split("\n")
    filtered = []
    for line in lines:
        stripped = line.strip()
        # Eliminar líneas de id, slug y preferred_slug a nivel del dashboard (indent ~2-4 espacios)
        if re.match(r"^\s{2,4}(id|slug|preferred_slug)\s*:", line):
            continue
        filtered.append(line)
    return "\n".join(filtered)


def replace_model_name(lookml: str) -> str:
    """
    Reemplaza cualquier referencia hardcodeada al modelo por la variable
    del manifest @{model_name}.
    
    Busca patrones como:
      model: "nombre_modelo"
      model: nombre_modelo
    Y los reemplaza por:
      model: "@{model_name}"
    """
    # Con comillas: model: "algo"
    lookml = re.sub(
        r'(model:\s*)"[^"]*"',
        r'\1"@{model_name}"',
        lookml,
    )
    # Sin comillas: model: algo (pero no si ya tiene @{})
    lookml = re.sub(
        r'(model:\s*)(?!["@])(\S+)',
        r'\1"@{model_name}"',
        lookml,
    )
    return lookml


def find_existing_file(dashboards_dir: str, dashboard_name: str) -> str | None:
    """
    Busca si ya existe un fichero para el dashboard dado.
    Busca por nombre exacto: <dashboard_name>.dashboard.lookml
    También busca dentro de los ficheros existentes por el nombre del dashboard.
    """
    # Búsqueda directa por nombre de fichero
    exact_path = os.path.join(dashboards_dir, f"{dashboard_name}.dashboard.lookml")
    if os.path.exists(exact_path):
        return exact_path

    # Búsqueda dentro de los ficheros existentes por el nombre del dashboard
    if os.path.isdir(dashboards_dir):
        for filename in os.listdir(dashboards_dir):
            if not filename.endswith(".dashboard.lookml"):
                continue
            filepath = os.path.join(dashboards_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                if re.search(
                    rf"^-\s+dashboard:\s+{re.escape(dashboard_name)}\s*$",
                    content,
                    re.MULTILINE,
                ):
                    return filepath
            except Exception:
                continue

    return None


def save_dashboard(filepath: str, lookml: str) -> None:
    """Guarda el LookML del dashboard en el fichero especificado."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(lookml)


def main():
    parser = argparse.ArgumentParser(
        description="Importa un dashboard de Looker como LookML limpio para el base_project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Ejemplo de uso:
              python update_dashboard.py --dashboard_id 42

            Variables de entorno necesarias:
              LOOKERSDK_BASE_URL       URL de la instancia de Looker
              LOOKERSDK_CLIENT_ID      Client ID de la API
              LOOKERSDK_CLIENT_SECRET  Client Secret de la API
        """),
    )
    parser.add_argument(
        "--dashboard_id",
        required=True,
        help="ID numérico del dashboard en Looker",
    )
    parser.add_argument(
        "--output_dir",
        default=None,
        help="Directorio de salida para los dashboards (por defecto: ../dashboards/ relativo al script)",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Muestra el resultado sin guardar el fichero",
    )

    args = parser.parse_args()

    # Directorio de dashboards por defecto
    if args.output_dir:
        dashboards_dir = args.output_dir
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dashboards_dir = os.path.join(script_dir, "..", "dashboards")
    dashboards_dir = os.path.abspath(dashboards_dir)

    # --- Paso 1: Obtener el LookML del dashboard ---
    print(f"📡 Conectando con Looker API...")
    sdk = looker_sdk.init40()

    print(f"📥 Obteniendo LookML del dashboard ID: {args.dashboard_id}")
    raw_lookml = get_dashboard_lookml(sdk, args.dashboard_id)

    # --- Paso 2: Detectar nombre del dashboard ---
    dashboard_name = extract_dashboard_name(raw_lookml)
    print(f"📋 Dashboard detectado: '{dashboard_name}'")

    # --- Paso 3: Transformar el LookML ---
    print("🔧 Limpiando id y slug...")
    cleaned = remove_id_and_slug(raw_lookml)

    print("🔧 Reemplazando modelo por @{{model_name}}...")
    cleaned = replace_model_name(cleaned)

    # --- Paso 4: Determinar fichero de destino ---
    existing = find_existing_file(dashboards_dir, dashboard_name)
    if existing:
        filepath = existing
        action = "ACTUALIZADO"
    else:
        filepath = os.path.join(dashboards_dir, f"{dashboard_name}.dashboard.lookml")
        action = "CREADO"

    # --- Paso 5: Guardar o mostrar ---
    if args.dry_run:
        print(f"\n--- DRY RUN: {action} → {filepath} ---")
        print(cleaned)
    else:
        save_dashboard(filepath, cleaned)
        print(f"\n✅ Dashboard {action}: {filepath}")

    # Resumen para GitHub Actions
    # Exponer outputs como variables de entorno de GitHub
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"dashboard_name={dashboard_name}\n")
            f.write(f"file_path={filepath}\n")
            f.write(f"action={action}\n")


if __name__ == "__main__":
    main()
