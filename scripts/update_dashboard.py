import argparse
import json
import os
import re
import sys
import looker_sdk

def clean_lookml(lookml: str) -> str:
    # Remove id/slug/preferred_slug (indentation 2-4 spaces = dashboard level)
    lines = lookml.split("\n")
    cleaned = "\n".join(line for line in lines if not re.match(r"^\s{2,4}(id|slug|preferred_slug)\s*:", line))

    # Replace model references (quoted and unquoted)
    cleaned = re.sub(r'(model:\s*)"[^"]*"', r'\1"@{model_name}"', cleaned)
    cleaned = re.sub(r'(model:\s*)(?!["@])(\S+)', r'\1"@{model_name}"', cleaned)

    return cleaned

def process_dashboard(sdk, dashboard_id: str) -> dict:

    print(f"Fetching LookML for dashboard ID: {dashboard_id}")
    raw_lookml = sdk.dashboard_lookml(dashboard_id).lookml

    # Use the dashboard title (set by the user in Looker) as the filename
    dash = sdk.dashboard(dashboard_id)
    dashboard_name = dash.title.replace(" ", "_").lower()
    print(f"Dashboard detected: '{dashboard_name}'")

    cleaned = clean_lookml(raw_lookml)

    # Determine output file
    filepath = os.path.join(os.path.abspath("dashboards"), f"{dashboard_name}.dashboard.lookml")
    action = "UPDATED" if os.path.exists(filepath) else "CREATED"

    # Save
    os.makedirs(os.path.abspath("dashboards"), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(cleaned)
    print(f"Dashboard {action}: {filepath}")

    return {
        "dashboard_id": dashboard_id,
        "dashboard_name": dashboard_name,
        "file_path": filepath,
        "action": action,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import dashboards from Looker as clean LookML for the Hub Project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dashboard_id",
        nargs="+",
        required=True,
        help="Dashboard ID(s) in Looker: numeric (42) or slug (8LWxYgffFEbPplvemGZcpD). Multiple IDs separated by space.",
    )

    args = parser.parse_args()

    # Connect to Looker API
    print("Connecting to Looker API")
    sdk = looker_sdk.init40()

    # Process each dashboard
    results = []
    errors = []
    for dashboard_id in args.dashboard_id:
        try:
            result = process_dashboard(sdk, dashboard_id)
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