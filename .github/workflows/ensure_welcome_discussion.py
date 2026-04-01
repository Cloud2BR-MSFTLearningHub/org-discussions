import json
import os
import sys

import requests

CONFIG_PATH = os.environ.get("ARCHIVE_CONFIG", "docs/discussions/archive.json")
TOKEN = os.environ.get("DISCUSSIONS_TOKEN") or os.environ.get("GITHUB_TOKEN")
WELCOME_TEMPLATE = os.environ.get("WELCOME_TEMPLATE", "docs/welcome-draft.md")
WELCOME_TITLE = os.environ.get("WELCOME_TITLE", "Welcome to the organization Discussions")
WELCOME_CATEGORY = os.environ.get("WELCOME_CATEGORY", "General")

QUERY_ORG = """
query($org: String!) {
  organization(login: $org) {
    id
    discussionCategories(first: 100) {
      nodes {
        id
        name
        slug
      }
    }
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

MUTATION_PIN = """
mutation($discussionId: ID!) {
  pinDiscussion(input: {discussionId: $discussionId}) {
    clientMutationId
  }
}
"""


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


def fetch_org_info(org, token):
    data = graphql_request(token, QUERY_ORG, {"org": org})
    org_data = data.get("organization")
    if not org_data:
        raise RuntimeError(f"Organization not found: {org}")
    return org_data


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


def find_category_id(categories, name):
    name_normalized = normalize_title(name)
    for category in categories:
        if normalize_title(category.get("name")) == name_normalized:
            return category.get("id")
    return None


def find_discussion_by_title(discussions, title, category_name=None):
    title_normalized = normalize_title(title)
    category_normalized = normalize_title(category_name) if category_name else None
    for item in discussions:
        if normalize_title(item.get("title")) == title_normalized:
            if category_normalized:
                item_category = item.get("category") or {}
                if normalize_title(item_category.get("name")) != category_normalized:
                    continue
            return item
    return None


def read_text(path):
    if not os.path.exists(path):
        print(f"Template not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().strip() + "\n"


def main():
    if not TOKEN:
        print("DISCUSSIONS_TOKEN or GITHUB_TOKEN is required")
        sys.exit(1)

    config = load_config(CONFIG_PATH)
    org = os.environ.get("ORG") or config.get("organization")
    if not org:
        print("Organization is missing from config")
        sys.exit(1)

    org_info = fetch_org_info(org, TOKEN)
    category_id = find_category_id(
        org_info.get("discussionCategories", {}).get("nodes", []), WELCOME_CATEGORY
    )
    if not category_id:
        raise RuntimeError(f"Category not found: {WELCOME_CATEGORY}")

    discussions = fetch_discussions(org, TOKEN)
    existing = find_discussion_by_title(discussions, WELCOME_TITLE, WELCOME_CATEGORY)

    if existing:
        discussion_id = existing.get("id")
        discussion_url = existing.get("url")
    else:
        body = read_text(WELCOME_TEMPLATE)
        create_data = graphql_request(
            TOKEN,
            MUTATION_CREATE,
            {
                "orgId": org_info.get("id"),
                "categoryId": category_id,
                "title": WELCOME_TITLE,
                "body": body,
            },
        )
        discussion = create_data.get("createDiscussion", {}).get("discussion")
        if not discussion:
            raise RuntimeError("Welcome discussion creation failed")
        discussion_id = discussion.get("id")
        discussion_url = discussion.get("url")
        print(f"Created welcome discussion: {discussion_url}")

    if discussion_id:
        try:
            graphql_request(TOKEN, MUTATION_PIN, {"discussionId": discussion_id})
            if discussion_url:
                print(f"Pinned welcome discussion: {discussion_url}")
        except RuntimeError as exc:
            print(f"Pin failed: {exc}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
