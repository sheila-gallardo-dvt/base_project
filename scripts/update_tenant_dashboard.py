import argparse
import json
import os
import re
import sys
import looker_sdk
import requests
import yaml

def parse_tenant_manifest(manifest_path: str) -> dict:
    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read()

    info = {}

    url_match = re.search(r'url:\s*"([^"]+)"', content)
    if url_match:
        info["base_repo_url"] = url_match.group(1)
        gh_match = re.search(r"github\.com/([^/]+)/([^/.]+)", info["base_repo_url"])
        if gh_match:
            info["base_owner"] = gh_match.group(1)
            info["base_repo"] = gh_match.group(2)

    ref_match = re.search(r'ref:\s*"([^"]+)"', content)
    if ref_match:
        info["base_ref"] = ref_match.group(1)

    model_match = re.search(
        r'override_constant:\s*model_name\s*\{[^}]*value:\s*"([^"]+)"',
        content,
        re.DOTALL,
    )
    if model_match:
        info["model_name"] = model_match.group(1)

    return info

def get_base_dashboard_from_github(owner: str, repo: str, ref: str, dashboard_name: str, gh_token: str) -> str | None:
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
        print(f"Dashboard '{dashboard_name}' not found in base@{ref}")
        return None
    else:
        print(f"Error {resp.status_code} fetching base dashboard: {resp.text}")
        return None

def parse_dashboard_yaml(lookml: str) -> dict:
    docs = yaml.safe_load(lookml)
    if isinstance(docs, list) and len(docs) > 0:
        return docs[0]
    return docs or {}

# YAML flow-style helpers for LookML output
class LookMLDumper(yaml.SafeDumper):
    pass

class FlowList(list):
    pass

class FlowDict(dict):
    pass

LookMLDumper.add_representer(FlowList, lambda dumper, data: dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True))
LookMLDumper.add_representer(FlowDict, lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data, flow_style=True))

def wrap_flow_structures(data):
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if k in ["extends", "fields", "sorts", "listens_to_filters", "listen"]:
                if isinstance(v, list):
                    new_dict[k] = FlowList(v)
                elif isinstance(v, dict):
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
    normalized = dict(element)

    for key in ("id", "slug", "preferred_slug"):
        normalized.pop(key, None)

    if remove_model:
        normalized.pop("model", None)

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
        "row": None,
        "col": None,
        "width": None,
        "height": None,
    }

    for key, default_val in noisy_defaults.items():
        if key in normalized and normalized[key] == default_val:
            normalized.pop(key)

    return normalized

def compare_elements(tenant_elements: list, base_elements: list) -> list:
    base_by_name = {el.get("name", ""): el for el in base_elements if el.get("name")}

    diff_elements = []
    for tenant_el in tenant_elements:
        name = tenant_el.get("name", "")
        tenant_norm = normalize_element(tenant_el, remove_model=True)

        if name not in base_by_name:
            diff_elements.append(tenant_el)
        else:
            base_norm = normalize_element(base_by_name[name], remove_model=True)
            if tenant_norm != base_norm:
                diff_elements.append(tenant_el)

    return diff_elements

def compare_filters(tenant_filters: list, base_filters: list) -> list:
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

def replace_model_name(lookml: str, target_model: str = "@{model_name}") -> str:
    if not target_model.startswith("@{"):
        replacement = f'"{target_model}"'
    else:
        replacement = target_model

    lookml = re.sub(r'(model:\s*)(?:\"[^\"]*\"|[@\w{}]+)', rf'\1{replacement}', lookml)
    return lookml

def dump_lookml_yaml(data: dict, tenant_model: str = "") -> str:
    wrapped = wrap_flow_structures(data)
    output = yaml.dump(
        [wrapped],
        Dumper=LookMLDumper,
        default_flow_style=False,
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

def generate_extends_dashboard(dashboard_name, tenant_name, base_dashboard_name, diff_elements, diff_filters, tenant_title="", tenant_model=""):
    dashboard = {
        "dashboard": f"{dashboard_name}",
        "title": tenant_title or f"{base_dashboard_name} - {tenant_name}",
        "extends": [base_dashboard_name],
    }

    if diff_elements:
        dashboard["elements"] = diff_elements
    if diff_filters:
        dashboard["filters"] = diff_filters

    return dump_lookml_yaml(dashboard, tenant_model)

def generate_standalone_dashboard(lookml: str, tenant_model: str = "") -> str:
    parsed = parse_dashboard_yaml(lookml)
    if not parsed:
        return lookml
    return dump_lookml_yaml(parsed, tenant_model)

def detect_base_dashboard_name(dashboards_dir: str, dashboard_name: str) -> str | None:
    filepath = os.path.join(dashboards_dir, f"{dashboard_name}.dashboard.lookml")
    if not os.path.exists(filepath):
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Flow style: extends: [name]
    match = re.search(r"extends:\s*\[(\w+)\]", content)
    if match:
        return match.group(1)

    # Block style: extends:\n  - name
    match = re.search(r"extends:\s*\n\s+-\s+(\w+)", content)
    if match:
        return match.group(1)

    return None

def process_dashboard(sdk, dashboard_id: str, args) -> dict:

    print(f"Fetching LookML for dashboard ID: {dashboard_id}")
    result = sdk.dashboard_lookml(dashboard_id)
    if not result.lookml:
        raise RuntimeError(f"Dashboard '{dashboard_id}' returned empty LookML.")
    raw_lookml = result.lookml

    # Use dashboard title as filename
    dash = sdk.dashboard(dashboard_id)
    dashboard_name = dash.title.replace(" ", "_").lower()
    print(f"Dashboard detected: '{dashboard_name}'")

    dashboards_dir = os.path.abspath("dashboards")
    manifest_path = os.path.join(".", "manifest.lkml")

    # Determine if this dashboard extends a base
    base_dashboard_name = args.base_dashboard
    if not base_dashboard_name:
        base_dashboard_name = detect_base_dashboard_name(dashboards_dir, dashboard_name)

    # Get tenant info from manifest
    tenant_model = args.tenant_name
    base_ref = "main"
    base_owner = args.base_repo_owner or ""
    base_repo = args.base_repo_name or ""

    if os.path.exists(manifest_path):
        manifest_info = parse_tenant_manifest(manifest_path)
        tenant_model = manifest_info.get("model_name", tenant_model)
        base_ref = manifest_info.get("base_ref", base_ref)
        if not base_owner:
            base_owner = manifest_info.get("base_owner", "")
        if not base_repo:
            base_repo = manifest_info.get("base_repo", "")

    gh_token = os.environ.get("GH_TOKEN", "")

    if base_dashboard_name:
        # EXTENDS case
        print(f"Dashboard extends: '{base_dashboard_name}' @ {base_ref}")

        base_lookml = get_base_dashboard_from_github(base_owner, base_repo, base_ref, base_dashboard_name, gh_token)

        if not base_lookml:
            print("Base dashboard not found. Generating as standalone.")
            output = generate_standalone_dashboard(raw_lookml)
        else:
            tenant_parsed = parse_dashboard_yaml(raw_lookml)
            base_parsed = parse_dashboard_yaml(base_lookml)

            diff_elements = compare_elements(tenant_parsed.get("elements", []), base_parsed.get("elements", []))
            diff_filters = compare_filters(tenant_parsed.get("filters", []), base_parsed.get("filters", []))

            print(f"Elements: {len(tenant_parsed.get('elements', []))} total, {len(base_parsed.get('elements', []))} base, {len(diff_elements)} new/modified")
            print(f"Filters diff: {len(diff_filters)}")

            output = generate_extends_dashboard(
                dashboard_name=dashboard_name,
                tenant_name=args.tenant_name,
                base_dashboard_name=base_dashboard_name,
                diff_elements=diff_elements,
                diff_filters=diff_filters,
                tenant_title=tenant_parsed.get("title", ""),
                tenant_model=tenant_model,
            )
    else:
        # NEW dashboard (no extend)
        print(f"New dashboard (no base extend). Model: {tenant_model}")
        output = generate_standalone_dashboard(raw_lookml, tenant_model=tenant_model)

    # Save
    filepath = os.path.join(dashboards_dir, f"{dashboard_name}.dashboard.lookml")
    action = "UPDATED" if os.path.exists(filepath) else "CREATED"

    os.makedirs(dashboards_dir, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Dashboard {action}: {filepath}")

    return {
        "dashboard_id": dashboard_id,
        "dashboard_name": dashboard_name,
        "is_extend": bool(base_dashboard_name),
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update tenant LookML dashboards with diff against the base project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dashboard_id", nargs="+", required=True,
        help="Dashboard ID(s) in Looker: numeric (42) or slug (8LWxYgffFEbPplvemGZcpD). Multiple IDs separated by space.")
    parser.add_argument("--tenant_name", required=True, help="Tenant name (e.g. tenant_1)")
    parser.add_argument("--base_dashboard", default=None,
        help="Name of the base dashboard it extends (auto-detected if not provided).")
    parser.add_argument("--base_repo_owner", default=None, help="GitHub owner of the base repo (overrides manifest).")
    parser.add_argument("--base_repo_name", default=None, help="GitHub name of the base repo (overrides manifest).")

    args = parser.parse_args()

    print("Connecting to Looker API")
    sdk = looker_sdk.init40()

    results = []
    errors = []
    for dashboard_id in args.dashboard_id:
        try:
            result = process_dashboard(sdk, dashboard_id, args)
            results.append(result)
        except Exception as e:
            print(f"\nError processing dashboard '{dashboard_id}': {e}")
            errors.append({"dashboard_id": dashboard_id, "error": str(e)})

    # GitHub Actions outputs
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"dashboard_names={json.dumps([r['dashboard_name'] for r in results])}\n")
            f.write(f"dashboard_count={len(results)}\n")

    if errors:
        sys.exit(1)
