"""
Real-size (1:1) A4 PDF export of cutlist layouts.

Each stock sheet layout is tiled onto as many A4 pages as needed so that,
once printed at 100% scale, the pages can be trimmed along the crop marks
and taped back together to rebuild the layout at real size. The printout
is ink-friendly: shapes are stroked only (no fill), with dimension labels
and a page number on every page for reassembly.
"""

import io
import math
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from flask_babel import gettext as _
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas

log = logging.getLogger(__name__)


@dataclass
class A4Tile:
    """One A4 page covering a rectangular region of a stock sheet"""
    sheet_number: int  # 1-based sheet number
    page_number: int   # 1-based global page number (across all sheets)
    row: int           # 1-based row in the tile grid, row 1 is the TOP of the sheet
    col: int           # 1-based column in the tile grid, column 1 is the LEFT of the sheet
    x0: float          # left edge of the covered region, in sheet coordinates (mm)
    y0: float          # bottom edge of the covered region, in sheet coordinates (mm)


class A4PdfExporter:
    """
    Generates a multi-page A4 PDF where each stock sheet is decomposed
    into a grid of A4 pages at real size (1 mm on the sheet = 1 mm on paper).
    """

    PAGE_WIDTH_MM = 210.0
    PAGE_HEIGHT_MM = 297.0

    def __init__(self, margin_mm: float = 10.0):
        """
        Args:
            margin_mm: white margin kept on every side of each A4 page.
                       The margin absorbs the printer's unprintable border and
                       is trimmed away (crop marks) before taping pages together.
        """
        self.margin_mm = float(margin_mm)
        self.printable_width_mm = self.PAGE_WIDTH_MM - 2 * self.margin_mm
        self.printable_height_mm = self.PAGE_HEIGHT_MM - 2 * self.margin_mm

    def grid_for_sheet(self, sheet_width: float, sheet_height: float) -> Tuple[int, int]:
        """
        Compute the A4 tile grid needed to cover a sheet at real size.

        Returns:
            (columns, rows) of A4 pages
        """
        cols = max(1, math.ceil(sheet_width / self.printable_width_mm))
        rows = max(1, math.ceil(sheet_height / self.printable_height_mm))
        return cols, rows

    def count_pages(self, sheets: List[Dict]) -> int:
        """Total number of A4 tile pages needed for all sheets (excluding the assembly plan page)"""
        total = 0
        for sheet in sheets:
            cols, rows = self.grid_for_sheet(float(sheet['width']), float(sheet['height']))
            total += cols * rows
        return total

    def generate(self, sheets: List[Dict], placements: List[Dict]) -> bytes:
        """
        Build the PDF.

        Args:
            sheets: list of dicts with at least 'index', 'width', 'height' (mm)
            placements: list of dicts with 'x', 'y', 'width', 'height',
                        'rotated', 'sheet_index' (mm, origin at bottom-left of the sheet)

        Returns:
            The PDF file content as bytes.
        """
        sheets = sorted(sheets, key=lambda s: s['index'])
        placements_by_sheet = {}
        for placement in placements:
            placements_by_sheet.setdefault(placement['sheet_index'], []).append(placement)

        tiles = self._build_tiles(sheets)
        total_pages = len(tiles)

        buffer = io.BytesIO()
        canvas = pdf_canvas.Canvas(buffer, pagesize=A4)
        canvas.setTitle(_('Cutlist layout — real size A4 export'))

        self._draw_assembly_plan(canvas, sheets, placements_by_sheet)

        for tile in tiles:
            sheet = sheets[tile.sheet_number - 1]
            sheet_placements = placements_by_sheet.get(sheet['index'], [])
            self._draw_tile_page(canvas, sheet, sheet_placements, tile, total_pages, len(sheets))

        canvas.save()
        return buffer.getvalue()

    # ------------------------------------------------------------------ #
    # Tiling                                                             #
    # ------------------------------------------------------------------ #

    def _build_tiles(self, sheets: List[Dict]) -> List[A4Tile]:
        """Build the ordered list of A4 tiles for all sheets (row 1 = top of sheet)"""
        tiles = []
        page_number = 1
        for sheet_pos, sheet in enumerate(sheets, start=1):
            sheet_height = float(sheet['height'])
            cols, rows = self.grid_for_sheet(float(sheet['width']), sheet_height)
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    tiles.append(A4Tile(
                        sheet_number=sheet_pos,
                        page_number=page_number,
                        row=row,
                        col=col,
                        x0=(col - 1) * self.printable_width_mm,
                        y0=sheet_height - row * self.printable_height_mm
                    ))
                    page_number += 1
        return tiles

    # ------------------------------------------------------------------ #
    # Assembly plan page                                                 #
    # ------------------------------------------------------------------ #

    def _draw_assembly_plan(self, canvas, sheets: List[Dict], placements_by_sheet: Dict):
        """
        First page: a small-scale overview of every sheet with the tile grid
        and the page number printed in each cell, used as an assembly guide.
        """
        margin = self.margin_mm * mm
        cursor_y = self.PAGE_HEIGHT_MM * mm - margin

        canvas.setFont('Helvetica-Bold', 14)
        canvas.drawString(margin, cursor_y - 14, _('Assembly plan'))
        canvas.setFont('Helvetica', 9)
        canvas.drawString(
            margin, cursor_y - 28,
            _('Print at real size (scale 1:1, no fit-to-page). '
              'Trim each page along the crop marks, then tape the pages together by number.'))
        cursor_y -= 45

        page_number = 1
        for sheet_pos, sheet in enumerate(sheets, start=1):
            sheet_width = float(sheet['width'])
            sheet_height = float(sheet['height'])
            cols, rows = self.grid_for_sheet(sheet_width, sheet_height)

            # Scale the sheet preview to fit the page width and a reasonable height
            scale = min((self.printable_width_mm * mm) / sheet_width, (110 * mm) / sheet_height)
            preview_w = sheet_width * scale
            preview_h = sheet_height * scale

            # New plan page if this preview does not fit
            if cursor_y - (preview_h + 12 * mm) < margin:
                canvas.showPage()
                cursor_y = self.PAGE_HEIGHT_MM * mm - margin

            canvas.setFont('Helvetica-Bold', 10)
            canvas.drawString(margin, cursor_y - 10, _(
                'Sheet %(num)d — %(width)s × %(height)s mm — %(pages)d pages',
                num=sheet_pos, width=self._fmt(sheet_width), height=self._fmt(sheet_height),
                pages=cols * rows))
            cursor_y -= 16

            origin_x = margin
            origin_y = cursor_y - preview_h

            # Sheet outline and pieces (thin strokes, no fill)
            canvas.setLineWidth(0.8)
            canvas.setStrokeColorRGB(0, 0, 0)
            canvas.rect(origin_x, origin_y, preview_w, preview_h)
            canvas.setLineWidth(0.3)
            canvas.setStrokeColorRGB(0.45, 0.45, 0.45)
            for placement in placements_by_sheet.get(sheet['index'], []):
                canvas.rect(origin_x + placement['x'] * scale,
                            origin_y + placement['y'] * scale,
                            placement['width'] * scale,
                            placement['height'] * scale)

            # Tile grid (dashed) with the page number in each cell
            canvas.setLineWidth(0.4)
            canvas.setStrokeColorRGB(0.2, 0.2, 0.2)
            canvas.setDash(3, 3)
            tile_w = self.printable_width_mm * scale
            tile_h = self.printable_height_mm * scale
            for col in range(1, cols):
                x = origin_x + col * tile_w
                canvas.line(x, origin_y, x, origin_y + preview_h)
            for row in range(1, rows):
                y = origin_y + preview_h - row * tile_h
                canvas.line(origin_x, y, origin_x + preview_w, y)
            canvas.setDash()

            canvas.setFont('Helvetica-Bold', 9)
            for row in range(1, rows + 1):
                for col in range(1, cols + 1):
                    cell_left = origin_x + (col - 1) * tile_w
                    cell_top = origin_y + preview_h - (row - 1) * tile_h
                    cell_right = min(cell_left + tile_w, origin_x + preview_w)
                    cell_bottom = max(cell_top - tile_h, origin_y)
                    canvas.drawCentredString((cell_left + cell_right) / 2,
                                             (cell_top + cell_bottom) / 2 - 3,
                                             str(page_number))
                    page_number += 1

            canvas.setStrokeColorRGB(0, 0, 0)
            cursor_y = origin_y - 10 * mm

        canvas.showPage()

    # ------------------------------------------------------------------ #
    # Real-size tile pages                                               #
    # ------------------------------------------------------------------ #

    def _draw_tile_page(self, canvas, sheet: Dict, placements: List[Dict],
                        tile: A4Tile, total_pages: int, total_sheets: int):
        """Draw one A4 page covering the tile region of the sheet at scale 1:1"""
        cols, rows = self.grid_for_sheet(float(sheet['width']), float(sheet['height']))

        self._draw_page_frame(canvas, tile, cols, rows, total_pages, total_sheets)
        self._draw_sheet_region(canvas, sheet, placements, tile)
        canvas.showPage()

    def _draw_page_frame(self, canvas, tile: A4Tile, cols: int, rows: int,
                         total_pages: int, total_sheets: int):
        """Draw margin annotations: header, page number, crop marks and neighbour page references"""
        margin = self.margin_mm * mm
        page_w = self.PAGE_WIDTH_MM * mm
        page_h = self.PAGE_HEIGHT_MM * mm

        # Header (top margin): position info on the left, page number on the right
        header_y = page_h - margin + 2 * mm
        canvas.setFont('Helvetica', 8)
        canvas.drawString(margin, header_y, _(
            'Sheet %(sheet)d/%(total_sheets)d — Row %(row)d/%(rows)d — Column %(col)d/%(cols)d',
            sheet=tile.sheet_number, total_sheets=total_sheets,
            row=tile.row, rows=rows, col=tile.col, cols=cols))
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawRightString(page_w - margin, header_y, _(
            'Page %(page)d/%(total)d', page=tile.page_number, total=total_pages))

        # Footer (bottom margin): big page number for quick sorting
        footer_y = margin - 5.5 * mm
        canvas.setFont('Helvetica-Bold', 12)
        canvas.drawRightString(page_w - margin, footer_y, str(tile.page_number))

        # Crop marks at the four corners of the printable area
        canvas.setLineWidth(0.3)
        mark = 6 * mm
        gap = 1 * mm
        for corner_x, dir_x in ((margin, -1), (page_w - margin, 1)):
            for corner_y, dir_y in ((margin, -1), (page_h - margin, 1)):
                canvas.line(corner_x + dir_x * gap, corner_y,
                            corner_x + dir_x * (gap + mark), corner_y)
                canvas.line(corner_x, corner_y + dir_y * gap,
                            corner_x, corner_y + dir_y * (gap + mark))

        # Neighbour page references in the margins (which page attaches on each side)
        canvas.setFont('Helvetica', 7)
        if tile.col > 1:
            canvas.drawCentredString(margin - 3.5 * mm, page_h / 2, '<< %d' % (tile.page_number - 1))
        if tile.col < cols:
            canvas.drawCentredString(page_w - margin + 3.5 * mm, page_h / 2, '%d >>' % (tile.page_number + 1))
        if tile.row > 1:
            canvas.drawCentredString(page_w / 2, header_y, '^ %d' % (tile.page_number - cols))
        if tile.row < rows:
            canvas.drawCentredString(page_w / 2, footer_y, 'v %d' % (tile.page_number + cols))

    def _draw_sheet_region(self, canvas, sheet: Dict, placements: List[Dict], tile: A4Tile):
        """Draw the sheet outline and pieces at scale 1:1, clipped to the tile region"""
        margin = self.margin_mm * mm

        canvas.saveState()
        clip = canvas.beginPath()
        clip.rect(margin, margin, self.printable_width_mm * mm, self.printable_height_mm * mm)
        canvas.clipPath(clip, stroke=0, fill=0)

        # Map sheet coordinates so that the tile origin lands on the printable area origin
        canvas.translate(margin - tile.x0 * mm, margin - tile.y0 * mm)

        # Stock sheet outline
        canvas.setLineWidth(1.2)
        canvas.rect(0, 0, float(sheet['width']) * mm, float(sheet['height']) * mm)

        # Pieces: outline only (no fill, ink-friendly)
        canvas.setLineWidth(0.6)
        for placement in placements:
            canvas.rect(placement['x'] * mm, placement['y'] * mm,
                        placement['width'] * mm, placement['height'] * mm)

        # Dimension labels, repeated on every page a piece appears on
        canvas.setFont('Helvetica', 10)
        tile_rect = (tile.x0, tile.y0,
                     tile.x0 + self.printable_width_mm, tile.y0 + self.printable_height_mm)
        for placement in placements:
            self._draw_piece_label(canvas, placement, tile_rect)

        canvas.restoreState()

    def _draw_piece_label(self, canvas, placement: Dict, tile_rect: Tuple[float, float, float, float]):
        """
        Draw the piece dimensions at the centre of the visible part of the piece
        on this page, so every page a piece spans carries its measurements.
        """
        visible = self._intersection(
            (placement['x'], placement['y'],
             placement['x'] + placement['width'], placement['y'] + placement['height']),
            tile_rect)
        if visible is None:
            return

        visible_w = visible[2] - visible[0]
        visible_h = visible[3] - visible[1]
        # Skip slivers where a label would not fit
        if visible_w < 30 or visible_h < 12:
            return

        label = '%s × %s' % (self._fmt(placement['width']), self._fmt(placement['height']))
        if placement.get('rotated'):
            label += ' (R)'
        center_x = (visible[0] + visible[2]) / 2 * mm
        center_y = (visible[1] + visible[3]) / 2 * mm
        canvas.drawCentredString(center_x, center_y - 4, label)

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _intersection(rect_a: Tuple[float, float, float, float],
                      rect_b: Tuple[float, float, float, float]) -> Optional[Tuple[float, float, float, float]]:
        """Intersection of two (x0, y0, x1, y1) rectangles, or None if they do not overlap"""
        x0 = max(rect_a[0], rect_b[0])
        y0 = max(rect_a[1], rect_b[1])
        x1 = min(rect_a[2], rect_b[2])
        y1 = min(rect_a[3], rect_b[3])
        if x0 >= x1 or y0 >= y1:
            return None
        return (x0, y0, x1, y1)

    @staticmethod
    def _fmt(value: float) -> str:
        """Format a millimetre value without trailing zeros (535.0 -> '535')"""
        return ('%g' % round(float(value), 2))
