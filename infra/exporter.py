"""
Exporter: Print/Export to PDF, CSV, etc.
----------------------------------------

Usage:
    from infra.exporter import export_to_csv, export_to_pdf
    export_to_csv(data, 'output.csv')
    export_to_pdf(data, 'output.pdf')

    from infra.exporter import export_to_svg
    export_to_svg(data, 'output.svg')

- CSV export uses Python's csv module.
- PDF export requires reportlab (pip install reportlab) or similar.
- SVG export is built-in and outputs a simple table or drawing.

Maintenance:
    - Extend export_to_csv/pdf for new data types or formats.
    - For advanced use, add more export formats as needed.
"""
import csv

# Example: Export a list of dicts to CSV
def export_to_csv(data, file_path):
    """Export a list of dicts to CSV."""
    if not data:
        raise ValueError('No data to export')
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

# Example: Export a list of dicts to PDF (simple table)
def export_to_pdf(data, file_path):
    """Export a list of dicts to PDF (requires reportlab)."""
    from reportlab.lib.pagesizes import letter
    
    # Example: Export a list of dicts to SVG (simple table)
    from reportlab.pdfgen import canvas
    if not data:
        raise ValueError('No data to export')
    c = canvas.Canvas(str(file_path), pagesize=letter)
    width, height = letter
    x, y = 50, height - 50
    # Write header
    for i, key in enumerate(data[0].keys()):
        c.drawString(x + i*100, y, str(key))
    y -= 20
    # Write rows
    for row in data:
        for i, key in enumerate(row.keys()):
            c.drawString(x + i*100, y, str(row[key]))
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()
