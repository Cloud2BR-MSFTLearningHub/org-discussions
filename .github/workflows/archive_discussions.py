import json
import os
import re
import sys
from datetime import datetime, timezone

import requests

CONFIG_PATH = os.environ.get("ARCHIVE_CONFIG", "docs/discussions/archive.json")
TOKEN = os.environ.get("DISCUSSIONS_TOKEN") or os.environ.get("GITHUB_TOKEN")

QUERY = """
query($org: String!, $number: Int!) {
  organization(login: $org) {
    discussion(number: $number) {
      title
      body
      url
      updatedAt
    }
  }
}
"""

REPLACEMENTS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2026": "...",
    "\u00a0": " ",
}


def normalize_ascii(text):
    for src, dst in REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text.encode("ascii", "ignore").decode("ascii")


def parse_org_and_number(url, default_org):
    if not url:
        return default_org, None

    org_match = re.search(r"github\.com/orgs/([^/]+)/discussions/(\d+)", url)
    if org_match:
        return org_match.group(1), int(org_match.group(2))

    repo_match = re.search(r"github\.com/([^/]+)/[^/]+/discussions/(\d+)", url)
    if repo_match:
        return repo_match.group(1), int(repo_match.group(2))

    number_match = re.search(r"/discussions/(\d+)", url)
    if number_match:
        return default_org, int(number_match.group(1))

    return default_org, None


def load_config(path):
    if not os.path.exists(path):
        print(f"Config not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_discussion(org, number, token):
    response = requests.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"bearer {token}"},
        json={"query": QUERY, "variables": {"org": org, "number": number}},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        print(f"GraphQL error for discussion {number}: {payload['errors']}")
        return None

    org_data = payload.get("data", {}).get("organization")
    if not org_data:
        print(f"Organization not found: {org}")
        return None

    return org_data.get("discussion")


def render_discussion(discussion):
    title = normalize_ascii(discussion.get("title", "Untitled"))
    body = normalize_ascii(discussion.get("body", "")).strip()
    url = normalize_ascii(discussion.get("url", ""))
    updated_at = discussion.get("updatedAt")

    if updated_at:
        last_updated = updated_at.split("T")[0]
    else:
        last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    parts = [
        f"# {title}",
        "",
        f"Source discussion: {url}",
        f"Last updated: {last_updated}",
        "",
        body,
        "",
    ]
    return "\n".join(parts)


def write_if_changed(path, content):
    existing = ""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            existing = handle.read()

    if existing == content:
        print(f"No changes: {path}")
        return False

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    print(f"Updated: {path}")
    return True


def main():
    if not TOKEN:
        print("DISCUSSIONS_TOKEN or GITHUB_TOKEN is required")
        sys.exit(1)

    config = load_config(CONFIG_PATH)
    default_org = config.get("organization")
    items = config.get("items", [])

    if not items:
        print("No items to archive")
        return

    for item in items:
        output_path = item.get("output_path")
        if not output_path:
            print("Skipping item with no output_path")
            continue

        org, number = parse_org_and_number(item.get("discussion_url", ""), default_org)
        if not org or not number:
            print(f"Skipping item with no discussion number: {output_path}")
            continue

        discussion = fetch_discussion(org, number, TOKEN)
        if not discussion:
            print(f"Discussion not found: {org} #{number}")
            continue

        content = render_discussion(discussion)
        write_if_changed(output_path, content)


if __name__ == "__main__":
    main()
