from urllib.parse import quote
import httpx
from app.integrations.sheets.oauth import access_token, write_enabled
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
    """Development-copy access; the only mutation is a guarded status-cell update."""
    def __init__(self, session, config, client=None, write=False):
        if config.spreadsheet_id == LIVE_SHEET_ID:
            raise NeedsInput("The real tracker is blocked. Configure a separate test copy.")
        self.config = config
        self.write = write
        if write and not write_enabled(config.spreadsheet_id):
            raise NeedsInput("Google Sheets write access is disabled for this copy.")
        self.token = access_token(session, require_write=write)
        self.client = client or httpx.Client(timeout=30)
        self.owned = client is None
        self.base = f"https://sheets.googleapis.com/v4/spreadsheets/{quote(config.spreadsheet_id, safe='')}/values/"

    def close(self):
        if self.owned:
            self.client.close()

    def request(self, method, range, **kwargs):
        if method.upper() != "GET" and not (method.upper() == "PUT" and getattr(self, "write", False) and write_enabled(self.config.spreadsheet_id)):
            raise NeedsInput("Google Sheets write access is disabled pending owner approval after read-only import testing.")
        try:
            response = self.client.request(method, self.base + quote(range, safe=""), headers={"Authorization": f"Bearer {self.token}"}, **kwargs)
            response.raise_for_status()
            if len(response.content) > 16_000_000:
                raise ValueError("Sheet too large")
            return response.json()
        except (httpx.HTTPError, ValueError):
            raise NeedsInput("Google Sheets write outcome is uncertain. Inspect the copy before creating another sync; no automatic retry was attempted." if method.upper() == "PUT" else "Google Sheets could not read the test copy. Check access and configuration.") from None

    def read(self):
        values = self.request("GET", quoted_tab(self.config.tab), params={"valueRenderOption": "FORMATTED_VALUE"}).get("values", [])
        formulas = self.request("GET", quoted_tab(self.config.tab), params={"valueRenderOption": "FORMULA"}).get("values", [])
        return values, formulas

    def cell(self, row, column, formula=False):
        range = f"{quoted_tab(self.config.tab)}!{column_name(column)}{row}"
        values = self.request("GET", range, params={"valueRenderOption": "FORMULA" if formula else "FORMATTED_VALUE"}).get("values", [])
        return values[0][0] if values and values[0] else ""

    def write_cell(self, row, column, value):
        if not getattr(self, "write", False) or not write_enabled(self.config.spreadsheet_id):
            raise NeedsInput("Google Sheets write access is disabled for this copy.")
        from app.integrations.sheets.sync import DISPLAY_STATUSES
        header = self.config.mapping.get("status")
        headers = self.request("GET", f"{quoted_tab(self.config.tab)}!{self.config.header_row}:{self.config.header_row}", params={"valueRenderOption": "FORMULA"}).get("values", [[]])[0]
        if not header or headers.count(header) != 1 or column != headers.index(header) + 1 or row <= self.config.header_row or value not in DISPLAY_STATUSES.values():
            raise NeedsInput("Only a mapped status cell below the header can be written.")
        target = f"{quoted_tab(self.config.tab)}!{column_name(column)}{row}"
        if str(self.cell(row, column, formula=True)).startswith("="):
            raise NeedsInput("A status formula cannot be overwritten.")
        return self.request("PUT", target, params={"valueInputOption": "RAW"}, json={"range": target, "majorDimension": "ROWS", "values": [[value]]})
