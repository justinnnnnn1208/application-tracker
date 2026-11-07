from urllib.parse import quote
import httpx
from app.integrations.sheets.oauth import access_token
from app.services.errors import NeedsInput

LIVE_SHEET_ID = "1UCZX9aj7Ls_EIgY231bhufQ0kQKjU0wGz_PP0RHT2dk"


def quoted_tab(tab):
    return "'" + tab.replace("'", "''") + "'"


def column_name(index):
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


class GoogleSheet:
    """Read-only access to a configured development copy. All mutations are blocked."""
    def __init__(self, session, config, client=None):
        if config.spreadsheet_id == LIVE_SHEET_ID:
            raise NeedsInput("The real tracker is blocked. Configure a separate test copy.")
        self.config = config
        self.token = access_token(session)
        self.client = client or httpx.Client(timeout=30)
        self.owned = client is None
        self.base = f"https://sheets.googleapis.com/v4/spreadsheets/{quote(config.spreadsheet_id, safe='')}/values/"

    def close(self):
        if self.owned:
            self.client.close()

    def request(self, method, range, **kwargs):
        if method.upper() != "GET":
            raise NeedsInput("Google Sheets write access is disabled pending owner approval after read-only import testing.")
        try:
            response = self.client.request(method, self.base + quote(range, safe=""), headers={"Authorization": f"Bearer {self.token}"}, **kwargs)
            response.raise_for_status()
            if len(response.content) > 16_000_000:
                raise ValueError("Sheet too large")
            return response.json()
        except (httpx.HTTPError, ValueError):
            raise NeedsInput("Google Sheets could not complete the operation. Check access to the test copy before retrying.") from None

    def read(self):
        values = self.request("GET", quoted_tab(self.config.tab), params={"valueRenderOption": "FORMATTED_VALUE"}).get("values", [])
        formulas = self.request("GET", quoted_tab(self.config.tab), params={"valueRenderOption": "FORMULA"}).get("values", [])
        return values, formulas

    def cell(self, row, column, formula=False):
        range = f"{quoted_tab(self.config.tab)}!{column_name(column)}{row}"
        values = self.request("GET", range, params={"valueRenderOption": "FORMULA" if formula else "FORMATTED_VALUE"}).get("values", [])
        return values[0][0] if values and values[0] else ""

    def write_cell(self, row, column, value):
        raise NeedsInput("Google Sheets write access is disabled pending owner approval after read-only import testing.")
