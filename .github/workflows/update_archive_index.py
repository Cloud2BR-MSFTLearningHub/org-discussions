import calendar
import json
import os
import re
import sys

import requests

CONFIG_PATH = os.environ.get("ARCHIVE_CONFIG", "docs/discussions/archive.json")
TOKEN = os.environ.get("DISCUSSIONS_TOKEN") or os.environ.get("GITHUB_TOKEN")

QUERY = """
query($org: String!, $after: String) {
  organization(login: $org) {
    discussions(first: 50, after: $after) {
      nodes {
        title
        url
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""

MONTH_NAME_TO_NUMBER = {
    calendar.month_name[i].lower(): i for i in range(1, 13) if calendar.month_name[i]
}


def load_config(path):
    if not os.path.exists(path):
        print(f"Config not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_title(value):
    return (value or "").strip().lower()


def parse_catalog_title(title):
    if not title:
        return None

    match = re.match(r"^Catalog Index - ([A-Za-z]+) (\d{4})$", title.strip())
    if not match:
        return None

    month_name = match.group(1).lower()
    month = MONTH_NAME_TO_NUMBER.get(month_name)
    if not month:
        return None

    return int(match.group(2)), month


def fetch_discussions(org, token):
    discussions = []
    cursor = None

    while True:
        payload = {"query": QUERY, "variables": {"org": org, "after": cursor}}
        response = requests.post(
            "https://api.github.com/graphql",
            headers={"Authorization": f"bearer {token}"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print(f"GraphQL error: {data['errors']}")
            sys.exit(1)

        org_data = data.get("data", {}).get("organization")
        if not org_data:
            print(f"Organization not found: {org}")
            sys.exit(1)

        connection = org_data.get("discussions")
        if not connection:
            break

        nodes = connection.get("nodes", [])
        discussions.extend(nodes)

        page_info = connection.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break

        cursor = page_info.get("endCursor")
        if len(discussions) >= 500:
            break

    return discussions


def write_if_changed(path, content):
    existing = ""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            existing = handle.read()

    if existing == content:
        print("Archive config unchanged")
        return False

    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)

    print("Archive config updated")
    return True


def main():
    if not TOKEN:
        print("DISCUSSIONS_TOKEN or GITHUB_TOKEN is required")
        sys.exit(1)

    config = load_config(CONFIG_PATH)
    org = config.get("organization")
    if not org:
        print("Organization is missing from config")
        sys.exit(1)

    items = config.get("items", [])
    if not items:
        print("No items to update")
        return

    discussions = fetch_discussions(org, TOKEN)
    title_map = {
        normalize_title(item.get("title")): item.get("url")
        for item in discussions
        if item.get("title") and item.get("url")
    }

    updated = False
    items_by_output = {
        item.get("output_path"): item for item in items if item.get("output_path")
    }
    existing_titles = {
        normalize_title(item.get("title_match"))
        for item in items
        if item.get("title_match")
    }

    for item in items:
        if item.get("discussion_url"):
            continue

        title_match = normalize_title(item.get("title_match"))
        if not title_match:
            continue

        matched_url = title_map.get(title_match)
        if not matched_url:
            continue

        item["discussion_url"] = matched_url
        if "notes" in item:
            del item["notes"]
        updated = True

    new_items = []
    for discussion in discussions:
        title = discussion.get("title")
        parsed = parse_catalog_title(title)
        if not parsed:
            continue

        year, month = parsed
        output_path = f"docs/discussions/catalog-index-{year}-{month:02d}.md"
        title_match = f"Catalog Index - {calendar.month_name[month]} {year}"
        title_key = normalize_title(title_match)

        existing_item = items_by_output.get(output_path)
        if existing_item:
            if not existing_item.get("title_match"):
                existing_item["title_match"] = title_match
                updated = True
            if discussion.get("url") and not existing_item.get("discussion_url"):
                existing_item["discussion_url"] = discussion.get("url")
                existing_item.pop("notes", None)
                updated = True
            continue

        if title_key in existing_titles:
            continue

        new_item = {
            "discussion_url": discussion.get("url") or "",
            "output_path": output_path,
            "title_match": title_match,
        }
        if not new_item["discussion_url"]:
            new_item["notes"] = "Discussion URL pending."
        new_items.append(new_item)
        existing_titles.add(title_key)

    if new_items:
        new_items.sort(key=lambda item: item.get("output_path", ""))
        items.extend(new_items)
        updated = True

    if not updated:
        print("No discussion URLs found to update")
        return

    content = json.dumps(config, indent=2, ensure_ascii=True) + "\n"
    write_if_changed(CONFIG_PATH, content)


if __name__ == "__main__":
    main()
