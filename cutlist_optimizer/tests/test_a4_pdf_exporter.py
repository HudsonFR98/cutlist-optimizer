"""
Tests for the real-size A4 PDF export of cutlist layouts.
"""

from cutlist_optimizer import create_app
from cutlist_optimizer.lib.a4_pdf_exporter import A4PdfExporter


def _sample_data(sheet_count=3):
    """Build a sample optimization result: sheets of 535 x 1000 mm with 3 pieces each"""
    sheets = [{'index': i, 'width': 535.0, 'height': 1000.0} for i in range(sheet_count)]
    placements = []
    for i in range(sheet_count):
        placements += [
            {'piece_id': 0, 'x': 0.0, 'y': 0.0, 'width': 535.0, 'height': 400.0,
             'rotated': False, 'sheet_index': i},
            {'piece_id': 1, 'x': 0.0, 'y': 400.0, 'width': 250.0, 'height': 550.0,
             'rotated': True, 'sheet_index': i},
            {'piece_id': 2, 'x': 250.0, 'y': 400.0, 'width': 120.0, 'height': 300.0,
             'rotated': False, 'sheet_index': i},
        ]
    return sheets, placements


def test_grid_computation():
    """
    Test the A4 tile grid computation.

    With the default 10 mm margin, the printable area of an A4 page is
    190 x 277 mm. A sheet is covered by ceil(width/190) columns and
    ceil(height/277) rows of A4 pages.

    Assertions:
        - A sheet smaller than the printable area needs a single page
        - A 535 x 1000 mm sheet needs 3 columns x 4 rows
        - Boundary values do not add an extra page
    """
    exporter = A4PdfExporter()

    assert exporter.grid_for_sheet(100, 200) == (1, 1)
    assert exporter.grid_for_sheet(535, 1000) == (3, 4)
    assert exporter.grid_for_sheet(190, 277) == (1, 1)
    assert exporter.grid_for_sheet(190.1, 277.1) == (2, 2)


def test_page_count():
    """
    Test the total tile page count over multiple sheets.

    Three sheets of 535 x 1000 mm each need 3 x 4 = 12 pages,
    so 36 pages in total (assembly plan pages excluded).
    """
    exporter = A4PdfExporter()
    sheets, _ = _sample_data(sheet_count=3)

    assert exporter.count_pages(sheets) == 36


def test_tile_ordering_and_regions():
    """
    Test that tiles are numbered left-to-right, top-to-bottom per sheet
    and that each tile covers the expected region of the sheet.

    Assertions:
        - Page numbers are sequential starting at 1
        - Row 1 covers the TOP of the sheet (highest y values)
        - Column 1 starts at x = 0
    """
    exporter = A4PdfExporter()
    sheets, _ = _sample_data(sheet_count=1)

    tiles = exporter._build_tiles(sheets)

    assert len(tiles) == 12
    assert [t.page_number for t in tiles] == list(range(1, 13))

    first = tiles[0]
    assert (first.row, first.col) == (1, 1)
    assert first.x0 == 0.0
    # Row 1 is the top band of the 1000 mm high sheet
    assert first.y0 == 1000.0 - exporter.printable_height_mm

    last = tiles[-1]
    assert (last.row, last.col) == (4, 3)
    assert last.y0 == 1000.0 - 4 * exporter.printable_height_mm


def test_pdf_generation():
    """
    Test that a valid multi-page PDF is generated.

    The export needs a request context because the PDF labels are
    translatable (Flask-Babel).

    Assertions:
        - Output is a PDF document
        - The document contains at least the 36 tile pages plus
          one assembly plan page
    """
    app = create_app()
    exporter = A4PdfExporter()
    sheets, placements = _sample_data(sheet_count=3)

    with app.test_request_context():
        pdf_bytes = exporter.generate(sheets, placements)

    assert pdf_bytes.startswith(b'%PDF')
    # Count page objects in the PDF (excluding the /Pages catalog nodes)
    import re
    page_objects = len(re.findall(rb'/Type\s*/Page[^s]', pdf_bytes))
    assert page_objects >= 37
