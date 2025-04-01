import os
import tempfile
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import chess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug info list for tracking application flow
debug_info = []

def add_debug_info(message):
    """Add a debug message to the global debug info list"""
    global debug_info
    debug_info.append(message)
    logger.info(message)

class VisualizationService:
    def __init__(self):
        pass

    def render_board_with_arrows(self, board, moves=None, last_move=None, flip=False):
        try:
            # Create arrows for suggested moves
            arrows = []
            if moves:
                for move in moves:
                    try:
                        # Convert move to arrow coordinates
                        if isinstance(move, chess.Move):
                            from_square = move.from_square
                            to_square = move.to_square
                            arrows.append(chess.svg.Arrow(from_square, to_square, color="blue"))
                        elif isinstance(move, str):
                            # Handle UCI format strings
                            move_obj = chess.Move.from_uci(move)
                            from_square = move_obj.from_square
                            to_square = move_obj.to_square
                            arrows.append(chess.svg.Arrow(from_square, to_square, color="blue"))
                    except Exception as e:
                        add_debug_info(f"Error creating arrow for move {move}: {str(e)}")
            
            # Add arrow for last move if provided
            if last_move:
                try:
                    if isinstance(last_move, chess.Move):
                        from_square = last_move.from_square
                        to_square = last_move.to_square
                        arrows.append(chess.svg.Arrow(from_square, to_square, color="green"))
                    elif isinstance(last_move, str):
                        move_obj = chess.Move.from_uci(last_move)
                        from_square = move_obj.from_square
                        to_square = move_obj.to_square
                        arrows.append(chess.svg.Arrow(from_square, to_square, color="green"))
                except Exception as e:
                    add_debug_info(f"Error creating arrow for last move {last_move}: {str(e)}")
            
            # Generate SVG
            svg = chess.svg.board(
                board=board,
                arrows=arrows,
                flipped=flip,
                size=400
            )
            
            return svg
        except Exception as e:
            add_debug_info(f"Error rendering board with arrows: {str(e)}")
            return None

    def generate_control_heatmap(self, board, perspective=chess.WHITE):
        try:
            # Create an 8x8 matrix for the heatmap
            heatmap_data = [[0 for _ in range(8)] for _ in range(8)]

            # Calculate control values for each square
            for square in chess.SQUARES:
                row, col = 7 - (square // 8), square % 8  # Convert to 0-indexed row, col

                # Count attackers for the square
                try:
                    attackers = len(board.attackers(perspective, square))
                    # Set control value
                    heatmap_data[row][col] = attackers
                except Exception as e:
                    add_debug_info(f"Error calculating attackers for square {square}: {str(e)}")
                    # Default to 0 if error
                    heatmap_data[row][col] = 0

            return heatmap_data
        except Exception as e:
            add_debug_info(f"Error generating control heatmap: {str(e)}")
            return [[0 for _ in range(8)] for _ in range(8)]

    def generate_piece_influence_map(self, board):
        try:
            # Create an 8x8 matrix for the influence map
            influence_data = [[0 for _ in range(8)] for _ in range(8)]

            # Calculate influence values for each square
            for square in chess.SQUARES:
                row, col = 7 - (square // 8), square % 8  # Convert to 0-indexed row, col

                try:
                    # Count white and black attackers
                    white_attackers = len(board.attackers(chess.WHITE, square))
                    black_attackers = len(board.attackers(chess.BLACK, square))

                    # Calculate influence (positive for white, negative for black)
                    influence_data[row][col] = white_attackers - black_attackers
                except Exception as e:
                    add_debug_info(f"Error calculating influence for square {square}: {str(e)}")
                    influence_data[row][col] = 0

            return influence_data
        except Exception as e:
            add_debug_info(f"Error generating piece influence map: {str(e)}")
            return [[0 for _ in range(8)] for _ in range(8)]

    def plot_heatmap(self, data, title="Heatmap", perspective="White"):
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
                # Create figure and axis
                plt.figure(figsize=(8, 8))

                # Determine colormap based on perspective
                if perspective == "White":
                    cmap = "Greens"
                elif perspective == "Black":
                    cmap = "Purples"
                else:  # Neutral for influence map
                    cmap = "coolwarm"

                # Create heatmap
                ax = sns.heatmap(
                    data,
                    cmap=cmap,
                    annot=True,
                    fmt="d",
                    linewidths=0.5,
                    square=True,
                    cbar=True
                )

                # Set title and labels
                plt.title(title)
                
                # Set axis labels (chess coordinates)
                ax.set_xticklabels(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
                ax.set_yticklabels(['8', '7', '6', '5', '4', '3', '2', '1'])
                
                # Save to temporary file
                plt.savefig(tmpfile.name, bbox_inches='tight')
                plt.close()
                
                return tmpfile.name
        except Exception as e:
            add_debug_info(f"Error plotting heatmap: {str(e)}")
            return None
