import calendar
import json
import os
import sys
from datetime import datetime, timezone

import requests

CONFIG_PATH = os.environ.get("ARCHIVE_CONFIG", "docs/discussions/archive.json")
TEMPLATE_PATH = os.environ.get(
    "TEMPLATE_PATH", "docs/discussions/templates/catalog-index-template.md"
)
TOKEN = os.environ.get("DISCUSSIONS_TOKEN") or os.environ.get("GITHUB_TOKEN")
CATEGORY_NAME = os.environ.get("DISCUSSION_CATEGORY", "Announcements")
LABEL_NAME = os.environ.get("DISCUSSION_LABEL", "documentation")
TARGET_MONTH = os.environ.get("TARGET_MONTH")
TARGET_YEAR = os.environ.get("TARGET_YEAR")

QUERY_ORG = """
query($org: String!) {
    organization(login: $org) {
        id
    }
}
"""

QUERY_DISCUSSIONS = """
query($org: String!, $after: String) {
  organization(login: $org) {
    discussions(first: 50, after: $after) {
      nodes {
        id
        title
        url
                category {
                    id
                    name
                }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""

QUERY_LABELS = """
query($org: String!) {
  organization(login: $org) {
    discussionLabels(first: 100) {
      nodes {
        id
        name
      }
    }
  }
}
"""

MUTATION_CREATE = """
mutation($orgId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
  createDiscussion(
    input: {
      organizationId: $orgId
      categoryId: $categoryId
      title: $title
      body: $body
    }
  ) {
    discussion {
      id
      url
    }
  }
}
"""

MUTATION_ADD_LABELS = """
mutation($labelableId: ID!, $labelIds: [ID!]!) {
  addLabelsToLabelable(input: {labelableId: $labelableId, labelIds: $labelIds}) {
    clientMutationId
  }
}
"""


def parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def determine_target_month_year():
    month = parse_int(TARGET_MONTH)
    year = parse_int(TARGET_YEAR)
    if month and year and 1 <= month <= 12:
        return year, month

    now = datetime.now(timezone.utc)
    month = now.month - 1
    year = now.year
    if month == 0:
        month = 12
        year -= 1
    return year, month


def graphql_request(token, query, variables):
    response = requests.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"bearer {token}"},
        json={"query": query, "variables": variables},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload.get("data", {})


def load_config(path):
    if not os.path.exists(path):
        print(f"Config not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_title(value):
    return (value or "").strip().lower()


def fetch_org_id(org, token):
    data = graphql_request(token, QUERY_ORG, {"org": org})
    org_data = data.get("organization")
    if not org_data or not org_data.get("id"):
        raise RuntimeError(f"Organization not found: {org}")
    return org_data.get("id")


def fetch_discussions(org, token):
    discussions = []
    cursor = None

    while True:
        data = graphql_request(token, QUERY_DISCUSSIONS, {"org": org, "after": cursor})
        org_data = data.get("organization")
        if not org_data:
            break

        connection = org_data.get("discussions")
        if not connection:
            break

        discussions.extend(connection.get("nodes", []))
        page_info = connection.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break

        cursor = page_info.get("endCursor")
        if len(discussions) >= 500:
            break

    return discussions


def find_category_id_from_discussions(discussions, name):
    name_normalized = normalize_title(name)
    for discussion in discussions:
        category = discussion.get("category") or {}
        if normalize_title(category.get("name")) == name_normalized:
            return category.get("id")
    return None


def find_discussion_by_title(discussions, title):
    title_normalized = normalize_title(title)
    for item in discussions:
        if normalize_title(item.get("title")) == title_normalized:
            return item
    return None


def find_config_discussion_url(items, title):
    title_normalized = normalize_title(title)
    for item in items:
        if normalize_title(item.get("title_match")) == title_normalized:
            return item.get("discussion_url")
    return None


def find_label_id(org, token, label_name):
    if not label_name:
        return None

    try:
        data = graphql_request(token, QUERY_LABELS, {"org": org})
    except RuntimeError as exc:
        print(f"Label lookup failed: {exc}")
        return None

    org_data = data.get("organization")
    if not org_data:
        return None

    labels = org_data.get("discussionLabels", {}).get("nodes", [])
    label_normalized = normalize_title(label_name)
    for label in labels:
        if normalize_title(label.get("name")) == label_normalized:
            return label.get("id")
    return None


def extract_last_catalog_section(content):
    if not content:
        return ""
    marker = "## Catalog"
    index = content.rfind(marker)
    if index == -1:
        return ""
    return content[index:].strip()


def read_text(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def default_catalog_section():
    return "\n".join(
        [
            "## Catalog",
            "",
            "| Category | Repositories |",
            "|---|---|",
            "| TODO | Add items here. |",
            "",
        ]
    )


def render_body(template, replacements):
    body = template
    for key, value in replacements.items():
        body = body.replace(key, value)
    return body.strip() + "\n"


def main():
    if not TOKEN:
        print("DISCUSSIONS_TOKEN or GITHUB_TOKEN is required")
        sys.exit(1)

    if not os.path.exists(TEMPLATE_PATH):
        print(f"Template not found: {TEMPLATE_PATH}")
        sys.exit(1)

    config = load_config(CONFIG_PATH)
    org = os.environ.get("ORG") or config.get("organization")
    if not org:
        print("Organization is missing from config")
        sys.exit(1)

    year, month = determine_target_month_year()
    month_name = calendar.month_name[month]
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    prev_month_name = calendar.month_name[prev_month]

    title = f"Catalog Index - {month_name} {year}"
    prev_title = f"Catalog Index - {prev_month_name} {prev_year}"
    last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    discussions = fetch_discussions(org, TOKEN)
    category_id = find_category_id_from_discussions(discussions, CATEGORY_NAME)
    if not category_id:
        raise RuntimeError(f"Category not found: {CATEGORY_NAME}")
    if find_discussion_by_title(discussions, title):
        print(f"Discussion already exists: {title}")
        return

    previous_url = find_config_discussion_url(config.get("items", []), prev_title)
    if not previous_url:
        previous_item = find_discussion_by_title(discussions, prev_title)
        if previous_item:
            previous_url = previous_item.get("url")

    if previous_url:
        previous_link = f"[{prev_month_name} {prev_year} discussion]({previous_url})"
    else:
        previous_link = f"{prev_month_name} {prev_year} discussion (link pending)"

    previous_archive_path = os.path.join(
        "docs", "discussions", f"catalog-index-{prev_year}-{prev_month:02d}.md"
    )
    previous_archive_raw = read_text(previous_archive_path)

    catalog_section = extract_last_catalog_section(previous_archive_raw)
    if not catalog_section:
        catalog_section = default_catalog_section()

    template = read_text(TEMPLATE_PATH)
    body = render_body(
        template,
        {
            "{{MONTH_NAME}}": month_name,
            "{{YEAR}}": str(year),
            "{{MONTH}}": f"{month:02d}",
            "{{LAST_UPDATED}}": last_updated,
            "{{PREVIOUS_MONTH_NAME}}": prev_month_name,
            "{{PREVIOUS_YEAR}}": str(prev_year),
            "{{PREVIOUS_DISCUSSION_LINK}}": previous_link,
            "{{CATALOG_SECTION}}": catalog_section,
        },
    )

    create_data = graphql_request(
        TOKEN,
        MUTATION_CREATE,
        {
            "orgId": fetch_org_id(org, TOKEN),
            "categoryId": category_id,
            "title": title,
            "body": body,
        },
    )

    discussion = create_data.get("createDiscussion", {}).get("discussion")
    if not discussion:
        raise RuntimeError("Discussion creation failed")

    discussion_id = discussion.get("id")
    discussion_url = discussion.get("url")
    print(f"Created discussion: {discussion_url}")

    label_id = find_label_id(org, TOKEN, LABEL_NAME)
    if label_id and discussion_id:
        try:
            graphql_request(
                TOKEN,
                MUTATION_ADD_LABELS,
                {"labelableId": discussion_id, "labelIds": [label_id]},
            )
            print(f"Applied label: {LABEL_NAME}")
        except RuntimeError as exc:
            print(f"Label apply failed: {exc}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
