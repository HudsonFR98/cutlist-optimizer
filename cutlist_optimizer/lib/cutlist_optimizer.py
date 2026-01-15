"""
Cutlist optimization algorithm for 2D rectangle packing.

This module implements a bottom-left-fill algorithm to minimize waste
when cutting pieces from stock sheets.
"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class Rectangle:
    """Represents a rectangle with position and dimensions"""
    width: float
    height: float
    x: float = 0.0
    y: float = 0.0
    id: Optional[int] = None
    rotated: bool = False
    
    def area(self) -> float:
        """Calculate the area of the rectangle"""
        return self.width * self.height
    
    def rotate(self):
        """Rotate the rectangle 90 degrees"""
        self.width, self.height = self.height, self.width
        self.rotated = not self.rotated
    
    def fits_in(self, container_width: float, container_height: float) -> bool:
        """Check if rectangle fits in container"""
        return self.width <= container_width and self.height <= container_height


@dataclass
class Piece:
    """Represents a piece to be cut with quantity"""
    width: float
    height: float
    quantity: int
    id: Optional[int] = None
    
    def area(self) -> float:
        """Calculate the area of the piece"""
        return self.width * self.height


@dataclass
class StockSheet:
    """Represents a stock sheet (available surface)"""
    width: float
    height: float
    quantity: int = 1
    id: Optional[int] = None
    
    def area(self) -> float:
        """Calculate the area of the stock sheet"""
        return self.width * self.height


@dataclass
class Placement:
    """Represents a placed piece on a sheet"""
    piece_id: Optional[int]
    x: float
    y: float
    width: float
    height: float
    rotated: bool
    sheet_index: int


@dataclass
class OptimizationResult:
    """Result of the optimization algorithm"""
    placements: List[Placement]
    sheets_used: List[Dict]
    total_waste: float
    total_waste_percentage: float
    efficiency: float
    total_pieces_placed: int
    total_pieces_requested: int
    unplaced_pieces: List[Piece]


class CutlistOptimizer:
    """
    Optimizes cutting layout to minimize waste using bottom-left-fill algorithm.
    """
    
    def __init__(self, stock_width: Optional[float] = None, stock_height: Optional[float] = None,
                 stock_sheets: Optional[List[StockSheet]] = None):
        """
        Initialize optimizer with stock sheet dimensions.
        
        Args:
            stock_width: Width of stock sheet in mm
            stock_height: Height of stock sheet in mm
        """
        self.stock_width = float(stock_width) if stock_width is not None else None
        self.stock_height = float(stock_height) if stock_height is not None else None
        self.stock_area = (self.stock_width * self.stock_height) if self.stock_width and self.stock_height else None
        self.stock_sheets = self._expand_stock_sheets(stock_sheets) if stock_sheets else None
    
    def optimize(self, pieces: List[Piece], stock_sheets: Optional[List[StockSheet]] = None) -> OptimizationResult:
        """
        Optimize cutting layout for given pieces.
        
        Args:
            pieces: List of pieces to cut with their quantities
            
        Returns:
            OptimizationResult with placements and statistics
        """
        # Expand pieces by quantity
        expanded_pieces = []
        for piece in pieces:
            for _ in range(piece.quantity):
                expanded_pieces.append(Piece(
                    width=piece.width,
                    height=piece.height,
                    quantity=1,
                    id=piece.id
                ))
        
        # Sort pieces by area (largest first) for better packing
        expanded_pieces.sort(key=lambda p: p.area(), reverse=True)
        
        # Calculate total area needed
        total_pieces_area = sum(p.area() for p in expanded_pieces)
        total_pieces_requested = len(expanded_pieces)
        
        # Pack pieces
        placements = []
        sheets_used = []
        current_sheet_index = 0
        unplaced_pieces = []

        available_sheets = None
        if stock_sheets is not None:
            available_sheets = self._expand_stock_sheets(stock_sheets)
        elif self.stock_sheets is not None:
            available_sheets = list(self.stock_sheets)
        
        for piece in expanded_pieces:
            placed = False
            
            # Try to place in existing sheets first
            for sheet_idx, sheet in enumerate(sheets_used):
                placement = self._try_place_piece(
                    piece, 
                    sheet['placed_rectangles'],
                    sheet['width'],
                    sheet['height'],
                    sheet_idx
                )
                if placement:
                    placements.append(placement)
                    sheet['placed_rectangles'].append(Rectangle(
                        width=placement.width,
                        height=placement.height,
                        x=placement.x,
                        y=placement.y,
                        id=placement.piece_id,
                        rotated=placement.rotated
                    ))
                    placed = True
                    break
            
            # If couldn't place, create new sheet
            if not placed:
                if available_sheets is not None:
                    selected_sheet = self._select_sheet_for_piece(piece, available_sheets)
                    if selected_sheet:
                        placement = self._place_on_new_sheet(
                            piece, selected_sheet.width, selected_sheet.height, current_sheet_index
                        )
                        if placement:
                            placements.append(placement)
                            sheets_used.append({
                                'index': current_sheet_index,
                                'width': selected_sheet.width,
                                'height': selected_sheet.height,
                                'placed_rectangles': [Rectangle(
                                    width=placement.width,
                                    height=placement.height,
                                    x=placement.x,
                                    y=placement.y,
                                    id=placement.piece_id,
                                    rotated=placement.rotated
                                )]
                            })
                            current_sheet_index += 1
                            available_sheets.remove(selected_sheet)
                            placed = True
                else:
                    placement = self._place_on_new_sheet(
                        piece, self.stock_width, self.stock_height, current_sheet_index
                    )
                    if placement:
                        placements.append(placement)
                        sheets_used.append({
                            'index': current_sheet_index,
                            'width': self.stock_width,
                            'height': self.stock_height,
                            'placed_rectangles': [Rectangle(
                                width=placement.width,
                                height=placement.height,
                                x=placement.x,
                                y=placement.y,
                                id=placement.piece_id,
                                rotated=placement.rotated
                            )]
                        })
                        current_sheet_index += 1
                        placed = True
                
                if not placed:
                    unplaced_pieces.append(piece)
                    log.warning(
                        f"Piece {piece.id} ({piece.width}x{piece.height}) does not fit in any stock sheet"
                    )
        
        # Calculate statistics
        total_sheets_area = sum(sheet['width'] * sheet['height'] for sheet in sheets_used)
        total_used_area = sum(p.width * p.height for p in placements)
        total_waste = max(total_sheets_area - total_used_area, 0)
        total_waste_percentage = (total_waste / total_sheets_area * 100) if total_sheets_area > 0 else 0
        efficiency = (total_used_area / total_sheets_area * 100) if total_sheets_area > 0 else 0
        
        return OptimizationResult(
            placements=placements,
            sheets_used=[{
                'index': sheet['index'],
                'width': sheet['width'],
                'height': sheet['height'],
                'used_area': sum(r.area() for r in sheet['placed_rectangles']),
                'waste_area': (sheet['width'] * sheet['height']) - sum(r.area() for r in sheet['placed_rectangles']),
                'waste_percentage': (((sheet['width'] * sheet['height']) - sum(r.area() for r in sheet['placed_rectangles'])) 
                                    / (sheet['width'] * sheet['height']) * 100) if (sheet['width'] * sheet['height']) > 0 else 0
            } for sheet in sheets_used],
            total_waste=total_waste,
            total_waste_percentage=total_waste_percentage,
            efficiency=efficiency,
            total_pieces_placed=len(placements),
            total_pieces_requested=total_pieces_requested,
            unplaced_pieces=unplaced_pieces
        )
    
    def _try_place_piece(self, piece: Piece, placed_rectangles: List[Rectangle], 
                        sheet_width: float, sheet_height: float, sheet_index: int) -> Optional[Placement]:
        """
        Try to place a piece on a sheet with existing rectangles.
        Uses bottom-left-fill algorithm.
        """
        # Try both orientations
        for rotated in [False, True]:
            width = piece.height if rotated else piece.width
            height = piece.width if rotated else piece.height
            
            if width > sheet_width or height > sheet_height:
                continue
            
            # Find best position using bottom-left-fill
            best_x, best_y = self._find_best_position(
                width, height, placed_rectangles, sheet_width, sheet_height
            )
            
            if best_x is not None and best_y is not None:
                # Check if placement is valid
                new_rect = Rectangle(width=width, height=height, 
                                    x=best_x, y=best_y)
                if self._is_valid_placement(new_rect, placed_rectangles):
                    return Placement(
                        piece_id=piece.id,
                        x=best_x,
                        y=best_y,
                        width=width,
                        height=height,
                        rotated=rotated,
                        sheet_index=sheet_index
                    )
        
        return None
    
    def _place_on_new_sheet(self, piece: Piece, sheet_width: float, sheet_height: float,
                            sheet_index: int) -> Optional[Placement]:
        """Place a piece on a new empty sheet"""
        # Try both orientations
        for rotated in [False, True]:
            width = piece.height if rotated else piece.width
            height = piece.width if rotated else piece.height
            
            if width <= sheet_width and height <= sheet_height:
                return Placement(
                    piece_id=piece.id,
                    x=0.0,
                    y=0.0,
                    width=width,
                    height=height,
                    rotated=rotated,
                    sheet_index=sheet_index
                )
        
        return None
    
    def _find_best_position(self, width: float, height: float, 
                           placed_rectangles: List[Rectangle], sheet_width: float,
                           sheet_height: float) -> Tuple[Optional[float], Optional[float]]:
        """
        Find the best position for a rectangle using bottom-left-fill.
        Returns (x, y) or (None, None) if no position found.
        """
        if not placed_rectangles:
            return (0.0, 0.0)
        
        # Generate candidate positions
        candidates = [(0.0, 0.0)]  # Always try bottom-left corner
        
        # Try positions adjacent to existing rectangles
        for rect in placed_rectangles:
            # Right of rectangle
            candidates.append((rect.x + rect.width, rect.y))
            # Top of rectangle
            candidates.append((rect.x, rect.y + rect.height))
        
        # Sort by y (bottom to top), then by x (left to right)
        candidates.sort(key=lambda pos: (pos[1], pos[0]))
        
        # Try each candidate position
        for x, y in candidates:
            if x + width <= sheet_width and y + height <= sheet_height:
                test_rect = Rectangle(width=width, height=height, x=x, y=y)
                if self._is_valid_placement(test_rect, placed_rectangles):
                    return (x, y)
        
        return (None, None)
    
    def _expand_stock_sheets(self, stock_sheets: List[StockSheet]) -> List[StockSheet]:
        """Expand stock sheets by quantity"""
        expanded = []
        for sheet in stock_sheets:
            quantity = int(sheet.quantity) if sheet.quantity else 1
            for _ in range(quantity):
                expanded.append(StockSheet(
                    width=float(sheet.width),
                    height=float(sheet.height),
                    quantity=1,
                    id=sheet.id
                ))
        return expanded
    
    def _select_sheet_for_piece(self, piece: Piece, available_sheets: List[StockSheet]) -> Optional[StockSheet]:
        """Select the smallest sheet that can fit the piece"""
        candidates = [sheet for sheet in available_sheets if self._sheet_can_fit_piece(piece, sheet)]
        if not candidates:
            return None
        return min(candidates, key=lambda sheet: sheet.area())
    
    def _sheet_can_fit_piece(self, piece: Piece, sheet: StockSheet) -> bool:
        """Check if a piece can fit on a sheet (considering rotation)"""
        return ((piece.width <= sheet.width and piece.height <= sheet.height) or
                (piece.height <= sheet.width and piece.width <= sheet.height))
    
    def _is_valid_placement(self, new_rect: Rectangle, 
                           placed_rectangles: List[Rectangle]) -> bool:
        """Check if a rectangle placement is valid (no overlaps)"""
        for rect in placed_rectangles:
            if self._rectangles_overlap(new_rect, rect):
                return False
        return True
    
    def _rectangles_overlap(self, rect1: Rectangle, rect2: Rectangle) -> bool:
        """Check if two rectangles overlap"""
        return not (rect1.x + rect1.width <= rect2.x or
                   rect2.x + rect2.width <= rect1.x or
                   rect1.y + rect1.height <= rect2.y or
                   rect2.y + rect2.height <= rect1.y)
    
    def to_json(self, result: OptimizationResult) -> Dict:
        """Convert optimization result to JSON-serializable dictionary"""
        data = {
            'placements': [
                {
                    'piece_id': p.piece_id,
                    'x': round(p.x, 2),
                    'y': round(p.y, 2),
                    'width': round(p.width, 2),
                    'height': round(p.height, 2),
                    'rotated': p.rotated,
                    'sheet_index': p.sheet_index
                }
                for p in result.placements
            ],
            'sheets': result.sheets_used,
            'statistics': {
                'total_sheets_used': len(result.sheets_used),
                'total_pieces_placed': result.total_pieces_placed,
                'total_pieces_requested': result.total_pieces_requested,
                'total_waste_mm2': round(result.total_waste, 2),
                'total_waste_percentage': round(result.total_waste_percentage, 2),
                'efficiency_percentage': round(result.efficiency, 2)
            }
        }
        
        if result.unplaced_pieces:
            data['unplaced_pieces'] = [
                {
                    'piece_id': p.id,
                    'width': round(p.width, 2),
                    'height': round(p.height, 2),
                    'quantity': p.quantity
                }
                for p in result.unplaced_pieces
            ]
        
        return data
