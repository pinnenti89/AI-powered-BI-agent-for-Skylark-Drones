import requests

MONDAY_URL = "https://api.monday.com/v2"

class MondayAPIError(Exception):
    pass

class MondayClient:
    def __init__(self, token: str):
        self.token = token

    def _request(self, query, variables=None):
        r = requests.post(
            MONDAY_URL,
            json={"query": query, "variables": variables or {}},
            headers={"Authorization": self.token, "Content-Type": "application/json"},
            timeout=30,
        )
        if r.status_code >= 400:
            raise MondayAPIError(f"HTTP {r.status_code}: {r.text[:500]}")
        body = r.json()
        if body.get("errors"):
            messages = "; ".join(e.get("message", "Unknown GraphQL error") for e in body["errors"])
            raise MondayAPIError(messages)
        return body["data"]

    def get_board(self, board_id: int):
        query = """
        query($boardIds:[ID!]) {
          boards(ids:$boardIds) {
            id
            name
            columns { id title type }
            items_page(limit:500) {
              cursor
              items {
                id
                name
                created_at
                updated_at
                column_values { id text value }
              }
            }
          }
        }
        """
        data = self._request(query, {"boardIds": [board_id]})
        boards = data.get("boards", [])
        if not boards:
            raise MondayAPIError(f"Board {board_id} was not found or is not accessible.")
        board = boards[0]
        items = board["items_page"]["items"]
        cursor = board["items_page"].get("cursor")

        # Cursor pagination follows monday.com's items_page/next_items_page model.
        while cursor:
            page = self._request(
                """
                query($cursor:String!) {
                  next_items_page(cursor:$cursor, limit:500) {
                    cursor
                    items {
                      id
                      name
                      created_at
                      updated_at
                      column_values { id text value }
                    }
                  }
                }
                """,
                {"cursor": cursor},
            )["next_items_page"]
            items.extend(page["items"])
            cursor = page.get("cursor")

        return {
            "id": board["id"],
            "name": board["name"],
            "columns": board["columns"],
            "items": items,
        }
