"""Small, disposable Excel fixtures; no private source workbook is required."""
import math
from openpyxl import Workbook
import pytest


@pytest.fixture
def excel_factory(tmp_path):
    def create(frame=None, headers=None, rows=None, sheet='Total Data', filename='customers.xlsx', header_row=1):
        workbook = Workbook()
        ws = workbook.active
        ws.title = sheet
        for _ in range(header_row):
            ws.append([None])
        ws.append(headers if headers is not None else list(frame.columns))
        records = rows if rows is not None else frame.itertuples(index=False, name=None)
        for row in records:
            ws.append([None if isinstance(value, float) and math.isnan(value) else value for value in row])
        path = tmp_path / filename
        workbook.save(path)
        workbook.close()
        return path
    return create
