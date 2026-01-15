""" webservices """

import logging

from flask import request, Blueprint, abort, jsonify
from flask_login import current_user
from cutlist_optimizer import dao
from cutlist_optimizer.lib.cutlist_optimizer import CutlistOptimizer, Piece, StockSheet


rest = Blueprint('rest', __name__)
log = logging.getLogger(__name__)


@rest.route('/optimize', methods=["POST"])
def optimize_cutlist():
    """
    Optimize cutlist layout to minimize waste.
    
    Expected JSON payload:
    {
        "stock_sheets": [  # Optional list of stock sheets (if omitted, use stock_width/stock_height)
            {
                "width": 1000.0,
                "height": 2000.0,
                "quantity": 2
            }
        ],
        "stock_width": 1000.0,  # Optional when stock_sheets is provided
        "stock_height": 2000.0,  # Optional when stock_sheets is provided
        "pieces": [  # List of pieces to cut
            {
                "width": 200.0,   # Width in mm
                "height": 300.0,   # Height in mm
                "quantity": 5      # Number of pieces needed
            },
            ...
        ],
        "save_cutlist": false,  # Optional: save cutlist and surfaces
        "cutlist_name": "My Cutlist"
    }
    
    Returns JSON with optimization results including placements and statistics.
    """
    try:
        data = request.get_json()
        
        if not data:
            abort(400, description="No JSON data provided")
        
        # Validate required fields
        if 'pieces' not in data or not isinstance(data['pieces'], list):
            abort(400, description="pieces must be a non-empty list")
        
        stock_sheets_data = data.get('stock_sheets')
        if stock_sheets_data is not None:
            if not isinstance(stock_sheets_data, list) or not stock_sheets_data:
                abort(400, description="stock_sheets must be a non-empty list")
        else:
            if 'stock_width' not in data or 'stock_height' not in data:
                abort(400, description="stock_width and stock_height are required when stock_sheets is not provided")
        
        stock_sheets = None
        stock_width = None
        stock_height = None
        if stock_sheets_data is not None:
            stock_sheets = []
            for idx, sheet_data in enumerate(stock_sheets_data):
                if 'width' not in sheet_data or 'height' not in sheet_data:
                    abort(400, description=f"Stock sheet {idx} must have width and height")
                
                width = float(sheet_data['width'])
                height = float(sheet_data['height'])
                quantity = int(sheet_data.get('quantity', 1))
                
                if width <= 0 or height <= 0:
                    abort(400, description=f"Stock sheet {idx}: width and height must be positive")
                
                if quantity <= 0:
                    abort(400, description=f"Stock sheet {idx}: quantity must be positive")
                
                stock_sheets.append(StockSheet(
                    width=width,
                    height=height,
                    quantity=quantity,
                    id=sheet_data.get('id', idx)
                ))
        else:
            stock_width = float(data['stock_width'])
            stock_height = float(data['stock_height'])
            
            if stock_width <= 0 or stock_height <= 0:
                abort(400, description="stock_width and stock_height must be positive")
        
        # Convert pieces to Piece objects
        pieces = []
        for idx, piece_data in enumerate(data['pieces']):
            if 'width' not in piece_data or 'height' not in piece_data:
                abort(400, description=f"Piece {idx} must have width and height")
            
            width = float(piece_data['width'])
            height = float(piece_data['height'])
            quantity = int(piece_data.get('quantity', 1))
            
            if width <= 0 or height <= 0:
                abort(400, description=f"Piece {idx}: width and height must be positive")
            
            if quantity <= 0:
                abort(400, description=f"Piece {idx}: quantity must be positive")
            
            pieces.append(Piece(
                width=width,
                height=height,
                quantity=quantity,
                id=piece_data.get('id', idx)
            ))
        
        if not pieces:
            abort(400, description="At least one piece is required")
        
        # Run optimization
        optimizer = CutlistOptimizer(stock_width=stock_width, stock_height=stock_height, stock_sheets=stock_sheets)
        result = optimizer.optimize(pieces, stock_sheets=stock_sheets)
        
        # Save cutlist if requested
        response_data = optimizer.to_json(result)
        if data.get('save_cutlist'):
            if not current_user.is_authenticated:
                abort(401, description="Authentication required to save cutlist")
            
            cutlist_name = data.get('cutlist_name')
            cutlist = dao.create_cutlist_with_surfaces(
                user_id=current_user.id,
                name=cutlist_name,
                surfaces=data['pieces']
            )
            response_data['saved_cutlist_id'] = cutlist.id
        
        # Convert to JSON
        return jsonify(response_data)
        
    except ValueError as e:
        log.error(f"Value error in optimize_cutlist: {e}")
        abort(400, description=f"Invalid numeric value: {str(e)}")
    except Exception as e:
        log.error(f"Error in optimize_cutlist: {e}", exc_info=True)
        abort(500, description=f"Internal server error: {str(e)}")


# @rest.route('/test', methods=["GET"])
# def get_test():
#     """ Exemple """

#     gene_id = request.values.get('gene_id')
#     gene = dao.get_gene(gene_id)
#     return jsonify(gene.to_json())
