import pytest
import csv
import os
from infra.exporter import export_to_csv

def test_export_to_csv(tmp_path):

    def test_export_to_svg(tmp_path):
        from infra.exporter import export_to_svg
        data = [
            {'name': 'A', 'value': 1},
            {'name': 'B', 'value': 2},
        ]
        file_path = tmp_path / 'test.svg'
        export_to_svg(data, file_path)
        assert file_path.exists()
        with open(file_path) as f:
            content = f.read()
        assert '<svg' in content
        assert 'A' in content and 'B' in content
    data = [
        {'name': 'A', 'value': 1},
        {'name': 'B', 'value': 2},
    ]
    file_path = tmp_path / 'test.csv'
    export_to_csv(data, file_path)
    assert file_path.exists()
    with open(file_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert rows[0]['name'] == 'A'
    assert rows[1]['value'] == '2'

# PDF export test (optional, requires reportlab)
def test_export_to_pdf(tmp_path):
    try:
        from infra.exporter import export_to_pdf
        data = [
            {'name': 'A', 'value': 1},
            {'name': 'B', 'value': 2},
        ]
        file_path = tmp_path / 'test.pdf'
        export_to_pdf(data, file_path)
        assert file_path.exists()
        assert os.path.getsize(file_path) > 0
    except ImportError:
        pytest.skip('reportlab not installed')
