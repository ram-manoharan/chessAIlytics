import streamlit as st
import chess
import chess.pgn
import chess.svg
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import re
import os
import time
import threading
import logging
import seaborn as sns
from io import StringIO
from datetime import datetime

# Import our chess analysis module
from chess_analysis import initialize_services, analyze_game_in_background, add_debug_info, debug_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="Chess Game Analyzer",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .move-button {
        margin: 2px;
    }
    .evaluation-bar {
        height: 20px;
        background: linear-gradient(to right, #4CAF50, #FFEB3B, #F44336);
        margin-bottom: 10px;
    }
    .evaluation-marker {
        height: 20px;
        width: 5px;
        background-color: black;
        position: relative;
    }
    .highlight-square {
        box-shadow: inset 0 0 0 3px red;
    }
    .debug-info {
        font-family: monospace;
        font-size: 0.8rem;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'move_history' not in st.session_state:
    st.session_state.move_history = []
if 'current_move_index' not in st.session_state:
    st.session_state.current_move_index = -1
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'pgn_text' not in st.session_state:
    st.session_state.pgn_text = ""
if 'analysis_in_progress' not in st.session_state:
    st.session_state.analysis_in_progress = False
if 'services' not in st.session_state:
    st.session_state.services = initialize_services()
if 'uci_moves' not in st.session_state:
    st.session_state.uci_moves = []
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False
if 'last_clicked_square' not in st.session_state:
    st.session_state.last_clicked_square = None
if 'selected_piece' not in st.session_state:
    st.session_state.selected_piece = None
if 'suggested_moves' not in st.session_state:
    st.session_state.suggested_moves = []
if 'flip_board' not in st.session_state:
    st.session_state.flip_board = False
if 'show_heatmap' not in st.session_state:
    st.session_state.show_heatmap = False
if 'show_influence' not in st.session_state:
    st.session_state.show_influence = False
if 'moves' not in st.session_state:
    st.session_state.moves = []
if 'current_move_index' not in st.session_state:
    st.session_state.current_move_index = -1
if 'game_info' not in st.session_state:
    st.session_state.game_info = None
if 'positions' not in st.session_state:
    st.session_state.positions = []
if 'move_notations' not in st.session_state:
    st.session_state.move_notations = []
if 'flip_board' not in st.session_state:
    st.session_state.flip_board = False
if 'analysis_depth' not in st.session_state:
    st.session_state.analysis_depth = "standard"
if 'show_arrows' not in st.session_state:
    st.session_state.show_arrows = True
if 'show_heatmap' not in st.session_state:
    st.session_state.show_heatmap = False
if 'show_influence' not in st.session_state:
    st.session_state.show_influence = False
if 'analysis_in_progress' not in st.session_state:
    st.session_state.analysis_in_progress = False
if 'services' not in st.session_state:
    st.session_state.services = None
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'uci_moves' not in st.session_state:
    st.session_state.uci_moves = []
# Helper functions
def get_svg_board(board, lastmove=None, squares=None, flipped=False):
    """Generate SVG for the current board position"""
    return chess.svg.board(
        board=board,
        lastmove=lastmove,
        flipped=flipped,
        squares=squares,
        size=400
    )

def svg_to_html(svg_str):
    """Convert SVG string to HTML for display"""
    b64 = base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')
    return f'<img src="data:image/svg+xml;base64,{b64}" />'

def reset_board():
    """Reset the board to starting position"""
    st.session_state.board = chess.Board()
    st.session_state.move_history = []
    st.session_state.current_move_index = -1
    st.session_state.analysis_results = {}
    st.session_state.pgn_text = ""
    st.session_state.uci_moves = []
    st.session_state.last_clicked_square = None
    st.session_state.selected_piece = None
    st.session_state.suggested_moves = []

def make_move(move):
    """Make a move on the board"""
    if isinstance(move, str):
        try:
            move = chess.Move.from_uci(move)
        except ValueError:
            try:
                move = st.session_state.board.parse_san(move)
            except ValueError:
                st.error(f"Invalid move: {move}")
                return False
    
    if move in st.session_state.board.legal_moves:
        # If we're not at the end of the move history, truncate it
        if st.session_state.current_move_index < len(st.session_state.move_history) - 1:
            st.session_state.move_history = st.session_state.move_history[:st.session_state.current_move_index + 1]
            st.session_state.uci_moves = st.session_state.uci_moves[:st.session_state.current_move_index + 1]
        
        # Make the move
        san = st.session_state.board.san(move)
        st.session_state.board.push(move)
        
        # Update move history
        st.session_state.move_history.append(san)
        st.session_state.uci_moves.append(move.uci())
        st.session_state.current_move_index += 1
        
        # Clear selection
        st.session_state.last_clicked_square = None
        st.session_state.selected_piece = None
        st.session_state.suggested_moves = []
        
        return True
    else:
        st.error(f"Illegal move: {move}")
        return False

def navigate_to_move(index):
    """Navigate to a specific move in the history"""
    if index >= -1 and index < len(st.session_state.move_history):
        # Reset board
        st.session_state.board = chess.Board()
        
        # Replay moves up to the selected index
        for i in range(index + 1):
            move_uci = st.session_state.uci_moves[i]
            st.session_state.board.push(chess.Move.from_uci(move_uci))
        
        st.session_state.current_move_index = index
        
        # Clear selection
        st.session_state.last_clicked_square = None
        st.session_state.selected_piece = None
        st.session_state.suggested_moves = []

def handle_square_click(square_name):
    """Handle clicking on a square of the chessboard"""
    try:
        square = chess.parse_square(square_name)
        
        # If a piece was already selected, try to make a move
        if st.session_state.selected_piece is not None:
            move = chess.Move(st.session_state.selected_piece, square)
            
            # Check if it's a promotion move
            if (st.session_state.board.piece_at(st.session_state.selected_piece) and 
                st.session_state.board.piece_at(st.session_state.selected_piece).piece_type == chess.PAWN and
                (square // 8 == 0 or square // 8 == 7)):
                # For simplicity, always promote to queen
                move = chess.Move(st.session_state.selected_piece, square, promotion=chess.QUEEN)
            
            # Try to make the move
            if make_move(move):
                return
            else:
                # If move failed, just update the selected square
                st.session_state.last_clicked_square = square
                piece = st.session_state.board.piece_at(square)
                if piece and piece.color == st.session_state.board.turn:
                    st.session_state.selected_piece = square
                else:
                    st.session_state.selected_piece = None
        else:
            # Update the selected square
            st.session_state.last_clicked_square = square
            piece = st.session_state.board.piece_at(square)
            if piece and piece.color == st.session_state.board.turn:
                st.session_state.selected_piece = square
            else:
                st.session_state.selected_piece = None
    
    except ValueError:
        st.error(f"Invalid square: {square_name}")

def generate_pgn():
    """Generate PGN text from the current game"""
    game = chess.pgn.Game()
    
    # Set headers
    game.headers["Event"] = "Chess Analysis"
    game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
    game.headers["White"] = "Player"
    game.headers["Black"] = "Opponent"
    game.headers["Result"] = "*"
    
    # Add moves
    node = game
    board = chess.Board()
    
    for uci_move in st.session_state.uci_moves:
        move = chess.Move.from_uci(uci_move)
        node = node.add_variation(move)
        board.push(move)
    
    # Set result based on board state
    if board.is_checkmate():
        result = "0-1" if board.turn == chess.WHITE else "1-0"
        game.headers["Result"] = result
    elif board.is_stalemate() or board.is_insufficient_material() or board.is_fifty_moves() or board.is_repetition():
        game.headers["Result"] = "1/2-1/2"
    
    return str(game)

def load_pgn(pgn_text):
    """Load a game from PGN text"""
    try:
        pgn = StringIO(pgn_text)
        game = chess.pgn.read_game(pgn)
        
        if not game:
            st.error("Invalid PGN format")
            return False
        
        # Reset board
        reset_board()
        
        # Extract headers if needed
        # game.headers...
        
        # Play through the moves
        board = chess.Board()
        for move in game.mainline_moves():
            san = board.san(move)
            board.push(move)
            
            # Update our state
            st.session_state.move_history.append(san)
            st.session_state.uci_moves.append(move.uci())
        
        # Set the board to the final position
        st.session_state.board = board
        st.session_state.current_move_index = len(st.session_state.move_history) - 1
        st.session_state.pgn_text = pgn_text
        
        return True
    
    except Exception as e:
        st.error(f"Error loading PGN: {str(e)}")
        return False

def start_analysis():
    """Start the analysis process in a background thread"""
    if st.session_state.analysis_in_progress:
        st.warning("Analysis already in progress")
        return
    
    # Generate PGN if needed
    if not st.session_state.pgn_text:
        st.session_state.pgn_text = generate_pgn()
    
    # Set analysis flag
    st.session_state.analysis_in_progress = True
    
    # Start analysis in a background thread
    analysis_thread = threading.Thread(
        target=run_analysis,
        args=(st.session_state.pgn_text, "standard")
    )
    analysis_thread.daemon = True
    analysis_thread.start()

def run_analysis(pgn_text, depth):
    """Run the analysis in a background thread"""
    try:
        # Perform analysis
        result = analyze_game_in_background(
            pgn_text,
            depth,
            st.session_state.services
        )
        
        # Store results
        if "error" not in result:
            # Store position analyses for quick access
            if "position_analyses" in result:
                st.session_state.analysis_results = result["position_analyses"]
            
            # Store UCI moves for better navigation
            if "uci_moves" in result:
                st.session_state.uci_moves = result["uci_moves"]
        else:
            add_debug_info(f"Analysis error: {result['error']}")
        
        st.session_state.analysis_in_progress = False
    
    except Exception as e:
        add_debug_info(f"Error in analysis thread: {str(e)}")
        st.session_state.analysis_in_progress = False

# Handle keyboard navigation
def handle_keyboard_navigation():
    # Create a JavaScript function to handle keyboard events
    st.markdown("""
    <script>
    // Function to log messages to console
    function logMessage(message) {
        console.log('[Chess Navigation] ' + message);
    }

    // Wait for DOM to fully load
    document.addEventListener('DOMContentLoaded', function() {
        logMessage('DOM fully loaded, setting up keyboard navigation');
        setupKeyboardNavigation();
    });

    // Set up keyboard navigation with retry mechanism
    function setupKeyboardNavigation() {
        logMessage('Setting up keyboard navigation');
        document.addEventListener('keydown', function(e) {
            logMessage('Key pressed: ' + e.key);
            if (e.key === 'ArrowLeft') {
                // Find the Previous button and click it
                const prevButtons = Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes('Previous'));
                if (prevButtons.length > 0) {
                    logMessage('Clicking Previous button');
                    prevButtons[0].click();
                } else {
                    logMessage('Previous button not found');
                }
            } else if (e.key === 'ArrowRight') {
                // Find the Next button and click it
                const nextButtons = Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes('Next'));
                if (nextButtons.length > 0) {
                    logMessage('Clicking Next button');
                    nextButtons[0].click();
                } else {
                    logMessage('Next button not found');
                }
            } else if (e.key === 'Home') {
                // Find the Start button and click it
                const startButtons = Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes('Start'));
                if (startButtons.length > 0) {
                    logMessage('Clicking Start button');
                    startButtons[0].click();
                } else {
                    logMessage('Start button not found');
                }
            } else if (e.key === 'End') {
                // Find the End button and click it
                const endButtons = Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes('End'));
                if (endButtons.length > 0) {
                    logMessage('Clicking End button');
                    endButtons[0].click();
                } else {
                    logMessage('End button not found');
                }
            }
        });

        logMessage('Keyboard navigation setup complete');
    }

    // Retry setup after a delay to ensure buttons are loaded
    setTimeout(function() {
        logMessage('Retrying keyboard navigation setup');
        setupKeyboardNavigation();
    }, 2000);

    // Additional retry with longer delay
    setTimeout(function() {
        logMessage('Final retry for keyboard navigation setup');
        setupKeyboardNavigation();
    }, 5000);
    </script>
    """, unsafe_allow_html=True)


# Main app layout
def main():

    # Enable keyboard navigation
    handle_keyboard_navigation()

    # App title
    st.title("ChessAIlytics")

    # Sidebar for controls
    with st.sidebar:
        st.header("Game Controls")

        # File uploader for PGN
        uploaded_file = st.file_uploader("Upload a PGN file", type="pgn")

        # Text area for PGN input
        pgn_text = st.text_area("Or paste PGN here", height=150)
        # Analysis depth selection
        st.session_state.analysis_depth = st.radio(
            "Analysis Depth",
            options=["standard", "deep"],
            index=0,
            help="Standard is faster, Deep provides more thorough analysis"
        )

        # Board orientation
        st.session_state.flip_board = st.checkbox("Flip Board", value=st.session_state.flip_board)

        # Visualization options
        st.session_state.show_arrows = st.checkbox("Show Suggested Moves", value=st.session_state.show_arrows)
        st.session_state.show_heatmap = st.checkbox("Show Control Heatmap", value=st.session_state.show_heatmap)
        st.session_state.show_influence = st.checkbox("Show Piece Influence", value=st.session_state.show_influence)

        # Analyze button
        analyze_button = st.button("Analyze Game", type="primary")

        # Reset button
        if st.button("Reset Analysis"):
            st.session_state.board = chess.Board()
            st.session_state.moves = []
            st.session_state.move_notations = []
            st.session_state.current_move_index = -1
            st.session_state.game_info = None
            st.session_state.positions = []
            st.session_state.analysis_in_progress = False
            st.session_state.analysis_results = {}
            st.session_state.uci_moves = []
            add_debug_info("Analysis reset")
            st.experimental_rerun()

    # Process uploaded file or pasted PGN
    if analyze_button and (uploaded_file is not None or pgn_text):
        st.session_state.analysis_in_progress = True
        add_debug_info("Starting analysis...")
        if uploaded_file is not None:
            pgn_text = uploaded_file.getvalue().decode("utf-8")
            add_debug_info("Loaded PGN from uploaded file")

        # Check for FEN tag
        fen_match = re.search(r'\[FEN "(.+?)"\]', pgn_text)
        custom_fen = None
        if fen_match:
            custom_fen = fen_match.group(1)
            add_debug_info(f"Processing PGN: {pgn_text}")
            add_debug_info(f"Found FEN: {custom_fen}")

            # Fix castling rights in FEN if needed
            if "HAha" in custom_fen:
                custom_fen = custom_fen.replace("HAha", "KQkq")
                add_debug_info(f"Fixed castling rights in FEN: {custom_fen}")

        # Parse the game
        pgn = StringIO(pgn_text)
        game = chess.pgn.read_game(pgn)

        if not game:
            st.error("Invalid PGN format")
            add_debug_info("Invalid PGN format")
            st.session_state.analysis_in_progress = False
        else:
            # Extract moves and positions
            moves = []
            positions = []
            move_notations = []
            uci_moves = []

            # Set up board with custom FEN if provided
            if custom_fen:
                try:
                    # Fix castling rights if needed
                    if "HAha" in custom_fen:
                        custom_fen = custom_fen.replace("HAha", "KQkq")

                    board = chess.Board(custom_fen)
                    add_debug_info(f"Set up board with custom FEN: {custom_fen}")
                except Exception as e:
                    add_debug_info(f"Error setting custom FEN: {str(e)}")
                    board = game.board()
            else:
                board = game.board()

            positions.append(board.fen())

            for move in game.mainline_moves():
                try:
                    san_move = board.san(move)
                    uci_move = move.uci()
                    move_notations.append(san_move)
                    uci_moves.append(uci_move)
                    board.push(move)
                    moves.append(move)
                    positions.append(board.fen())
                except Exception as e:
                    add_debug_info(f"Error processing move: {str(e)}")
                    continue

            # Update session state
            if custom_fen:
                try:
                    # Fix castling rights if needed
                    if "HAha" in custom_fen:
                        custom_fen = custom_fen.replace("HAha", "KQkq")
                    st.session_state.board = chess.Board(custom_fen)
                    add_debug_info(f"Set initial board position: {custom_fen}")
                except Exception as e:
                    add_debug_info(f"Error setting initial board position: {str(e)}")
                    st.session_state.board = chess.Board()
            else:
                st.session_state.board = chess.Board()
                add_debug_info(f"Set initial board position: {st.session_state.board.fen()}")

            st.session_state.moves = moves
            st.session_state.move_notations = move_notations
            st.session_state.positions = positions
            st.session_state.current_move_index = -1
            st.session_state.uci_moves = uci_moves

            add_debug_info(f"Loaded game with {len(moves)} moves")

            # Run analysis directly (no threading to avoid session state issues)
            result = analyze_game_in_background(pgn_text, st.session_state.analysis_depth, st.session_state.services)

            # Store analysis result
            if "error" not in result:
                st.session_state.game_info = result
                add_debug_info("Analysis completed and stored in session state")

                # Store position analyses for quick access
                #if "position_analyses" in result:
                 #   st.session_state.analysis_results = result["position_analyses"]

                # Store UCI moves for better navigation
                if "uci_moves" in result:
                    st.session_state.uci_moves = result["uci_moves"]
            else:
                add_debug_info(f"Analysis error: {result['error']}")

            st.session_state.analysis_in_progress = False

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        # Display navigation controls and chessboard if moves are available
        if st.session_state.moves:
            # Navigation controls
            st.subheader("Navigation")
            nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)

            with nav_col1:
                if st.button("⏮️ Start", key="start_button"):
                    add_debug_info("Start button clicked")
                    st.session_state.current_move_index = -1

                    # Reset board to initial position
                    if st.session_state.positions and len(st.session_state.positions) > 0:
                        try:
                            # Get the initial FEN position
                            initial_fen = st.session_state.positions[0]
                            st.session_state.board = chess.Board(initial_fen)
                            add_debug_info(f"Set board to initial position: {initial_fen}")
                        except Exception as e:
                            add_debug_info(f"Error setting initial board position: {str(e)}")
                            st.session_state.board = chess.Board()

            with nav_col2:
                if st.button("⏪ Previous", key="prev_button"):
                    add_debug_info("Previous button clicked")
                    if st.session_state.current_move_index >= 0:
                        st.session_state.current_move_index -= 1
                        add_debug_info(f"Moved to move index: {st.session_state.current_move_index}")

                        # Set board directly to the position after this move
                        position_index = st.session_state.current_move_index + 1
                        if position_index >= 0 and position_index < len(st.session_state.positions):
                            try:
                                st.session_state.board = chess.Board(st.session_state.positions[position_index])
                                add_debug_info(f"Set board to position {position_index}: {st.session_state.positions[position_index]}")
                            except Exception as e:
                                add_debug_info(f"Error setting board position: {str(e)}")
                                # Fallback: reset and replay moves
                                try:
                                    st.session_state.board = chess.Board(st.session_state.positions[0])
                                    for i in range(st.session_state.current_move_index + 1):
                                        st.session_state.board.push(st.session_state.moves[i])
                                    add_debug_info("Fallback: Reset and replayed moves")
                                except Exception as e2:
                                    add_debug_info(f"Error in fallback move replay: {str(e2)}")
                    else:
                        add_debug_info("Already at first move")
                        # Ensure we're at the initial position
                        if st.session_state.positions and len(st.session_state.positions) > 0:
                            try:
                                st.session_state.board = chess.Board(st.session_state.positions[0])
                                add_debug_info(f"Reset to initial position: {st.session_state.positions[0]}")
                            except Exception as e:
                                add_debug_info(f"Error resetting to initial position: {str(e)}")

            with nav_col3:
                current_move = st.session_state.current_move_index + 1
                total_moves = len(st.session_state.moves)
                st.markdown(f"<div class='move-display'>Move {current_move}/{total_moves}</div>", unsafe_allow_html=True)

            with nav_col4:
                if st.button("⏩ Next", key="next_button"):
                    add_debug_info("Next button clicked")
                    if st.session_state.current_move_index < len(st.session_state.moves) - 1:
                        st.session_state.current_move_index += 1
                        add_debug_info(f"Moved to move index: {st.session_state.current_move_index}")

                        # Set board directly to the position after this move
                        position_index = st.session_state.current_move_index + 1
                        if position_index < len(st.session_state.positions):
                            try:
                                st.session_state.board = chess.Board(st.session_state.positions[position_index])
                                add_debug_info(f"Set board to position {position_index}: {st.session_state.positions[position_index]}")
                            except Exception as e:
                                add_debug_info(f"Error setting board position: {str(e)}")
                                # Fallback: try to apply the move to current board
                                try:
                                    move = st.session_state.moves[st.session_state.current_move_index]
                                    st.session_state.board.push(move)
                                    add_debug_info(f"Applied move: {move}")
                                except Exception as e2:
                                    add_debug_info(f"Error applying move: {str(e2)}")
                                    # Last resort: reset and replay all moves
                                    try:
                                        st.session_state.board = chess.Board(st.session_state.positions[0])
                                        for i in range(st.session_state.current_move_index + 1):
                                            st.session_state.board.push(st.session_state.moves[i])
                                        add_debug_info("Last resort: Reset and replayed all moves")
                                    except Exception as e3:
                                        add_debug_info(f"Error in last resort move replay: {str(e3)}")
                    else:
                        add_debug_info("Already at last move")

            with nav_col5:
                if st.button("⏭️ End", key="end_button"):
                    add_debug_info("End button clicked")
                    st.session_state.current_move_index = len(st.session_state.moves) - 1
                    add_debug_info(f"Moved to final move index: {st.session_state.current_move_index}")

                    # Set board directly to the final position
                    if st.session_state.positions and len(st.session_state.positions) > st.session_state.current_move_index + 1:
                        try:
                            final_position = st.session_state.positions[-1]
                            st.session_state.board = chess.Board(final_position)
                            add_debug_info(f"Set board to final position: {final_position}")
                        except Exception as e:
                            add_debug_info(f"Error setting final board position: {str(e)}")
                            # Fallback: reset and replay all moves
                            try:
                                st.session_state.board = chess.Board(st.session_state.positions[0])
                                for move in st.session_state.moves:
                                    st.session_state.board.push(move)
                                add_debug_info("Fallback: Reset and replayed all moves to final position")
                            except Exception as e2:
                                add_debug_info(f"Error in fallback move replay: {str(e2)}")

            # Display current move in algebraic notation
            if st.session_state.current_move_index >= 0 and len(st.session_state.move_notations) > st.session_state.current_move_index:
                current_notation = st.session_state.move_notations[st.session_state.current_move_index]
                move_number = (st.session_state.current_move_index // 2) + 1
                is_white = st.session_state.current_move_index % 2 == 0
                color = "White" if is_white else "Black"
                notation_display = f"{move_number}.{'' if is_white else '..'} {current_notation} ({color})"
                st.markdown(f"<div class='current-move-notation'>{notation_display}</div>", unsafe_allow_html=True)
                add_debug_info(f"Displayed current move notation: {notation_display}")

        # Display the chessboard
        st.subheader("Chessboard")

        # Get last move for highlighting
        last_move = None
        if st.session_state.current_move_index >= 0 and st.session_state.moves:
            last_move = st.session_state.moves[st.session_state.current_move_index]
            add_debug_info(f"Last move for highlighting: {last_move}")

        # Get suggested moves for arrows
        suggested_moves = []
        if st.session_state.show_arrows and st.session_state.positions and st.session_state.services:
            try:
                current_fen = st.session_state.board.fen()
                add_debug_info(f"Getting suggested moves for position: {current_fen}")

                # Check if we already have analysis for this position
                if current_fen in st.session_state.analysis_results:
                    eval_result = st.session_state.analysis_results[current_fen]
                else:
                    # Get stockfish evaluation for this position
                    eval_result = st.session_state.services["stockfish_service"].analyze_position(current_fen, multi_pv=3)
                    # Store for future use
                    st.session_state.analysis_results[current_fen] = eval_result

                if "error" not in eval_result and "top_moves" in eval_result:
                    for move_info in eval_result["top_moves"]:
                        # Extract first move from UCI format
                        first_move = move_info["Move"]
                        try:
                            move = chess.Move.from_uci(first_move)
                            suggested_moves.append(move)
                            add_debug_info(f"Added suggested move: {first_move}")
                        except ValueError as e:
                            add_debug_info(f"Error parsing suggested move {first_move}: {str(e)}")
                else:
                    add_debug_info(f"Error getting suggested moves: {eval_result.get('error', 'Unknown error')}")
            except Exception as e:
                add_debug_info(f"Error getting suggested moves: {str(e)}")

        # Render the chessboard
        try:
            if st.session_state.show_arrows and suggested_moves and st.session_state.services:
                # Render with arrows for suggested moves
                add_debug_info("Rendering board with arrows")
                board_svg = st.session_state.services["visualization_service"].render_board_with_arrows(
                    st.session_state.board,
                    moves=suggested_moves,
                    last_move=last_move,
                    flip=st.session_state.flip_board
                )
            else:
                # Render standard board
                add_debug_info("Rendering standard board")
                board_svg = chess.svg.board(
                    st.session_state.board,
                    lastmove=last_move,
                    size=400,
                    flipped=st.session_state.flip_board
                )

            # Display the board
            st.markdown(board_svg, unsafe_allow_html=True)
            add_debug_info("Board displayed successfully")
        except Exception as e:
            add_debug_info(f"Error displaying board: {str(e)}")
            st.error(f"Error displaying chessboard: {str(e)}")

        # Display heatmaps if enabled
        if (st.session_state.show_heatmap or st.session_state.show_influence) and st.session_state.services:
            st.subheader("Board Analysis")

            viz_col1, viz_col2 = st.columns(2)

            with viz_col1:
                if st.session_state.show_heatmap:
                    st.markdown("**Board Control Heatmap**")
                    # Generate heatmap for white
                    try:
                        white_control = st.session_state.services["visualization_service"].generate_control_heatmap(
                            st.session_state.board,
                            perspective=chess.WHITE
                        )
                        white_heatmap_file = st.session_state.services["visualization_service"].plot_heatmap(
                            white_control,
                            title="White's Board Control",
                            perspective="White"
                        )
                        if white_heatmap_file:
                            st.image(white_heatmap_file)
                            add_debug_info("White's heatmap displayed successfully")
                        else:
                            st.error("Error generating White's heatmap")
                            add_debug_info("Error generating White's heatmap")
                    except Exception as e:
                        st.error(f"Error generating White's heatmap: {str(e)}")
                        add_debug_info(f"Error generating White's heatmap: {str(e)}")

            with viz_col2:
                if st.session_state.show_heatmap:
                    st.markdown("**Board Control Heatmap**")
                    # Generate heatmap for black
                    try:
                        black_control = st.session_state.services["visualization_service"].generate_control_heatmap(
                            st.session_state.board,
                            perspective=chess.BLACK
                        )
                        black_heatmap_file = st.session_state.services["visualization_service"].plot_heatmap(
                            black_control,
                            title="Black's Board Control",
                            perspective="Black"
                        )
                        if black_heatmap_file:
                            st.image(black_heatmap_file)
                            add_debug_info("Black's heatmap displayed successfully")
                        else:
                            st.error("Error generating Black's heatmap")
                            add_debug_info("Error generating Black's heatmap")
                    except Exception as e:
                        st.error(f"Error generating Black's heatmap: {str(e)}")
                        add_debug_info(f"Error generating Black's heatmap: {str(e)}")

            if st.session_state.show_influence:
                st.markdown("**Piece Influence Map**")
                # Generate influence map
                try:
                    influence_grid = st.session_state.services["visualization_service"].generate_piece_influence_map(
                        st.session_state.board
                    )
                    influence_file = st.session_state.services["visualization_service"].plot_heatmap(
                        influence_grid,
                        title="Piece Influence (Red: White, Blue: Black)",
                        perspective="Neutral"
                    )
                    if influence_file:
                        st.image(influence_file)
                        add_debug_info("Influence map displayed successfully")
                    else:
                        st.error("Error generating influence map")
                        add_debug_info("Error generating influence map")
                except Exception as e:
                    st.error(f"Error generating influence map: {str(e)}")
                    add_debug_info(f"Error generating influence map: {str(e)}")

    with col2:
        # Show loading indicator if analysis is in progress
        if st.session_state.analysis_in_progress:
            st.info("Analysis in progress... Please wait.")
            add_debug_info("Showing analysis in progress indicator")

        # Display analysis results if available
        if st.session_state.game_info:
            add_debug_info("Displaying game analysis results")
            # Display opening information
            #if "opening" in st.session_state.game_info:
                #st.subheader("Opening Information")
                #opening = st.session_state.game_info["opening"]
                #st.markdown(f"**Name:** {opening['name']}")
                #st.markdown(f"**ECO Code:** {opening['eco']}")
                #st.markdown(f"**Description:** {opening['description']}")
                #add_debug_info(f"Displayed opening information: {opening['name']}")


            # Display current position analysis
            if st.session_state.board and st.session_state.moves and st.session_state.services:
                st.subheader("Current Position Analysis")
                current_fen = st.session_state.board.fen()
                add_debug_info(f"Analyzing current position: {current_fen}")

                # Check if we already have analysis for this position
                if current_fen in st.session_state.analysis_results:
                    eval_result = st.session_state.analysis_results[current_fen]
                    add_debug_info("Using cached analysis for current position")
                else:
                    # Get Stockfish evaluation
                    #eval_result = st.session_state.services["stockfish_service"].analyze_position(current_fen)
                    eval_result = st.session_state.services["ai_service"].analyze_position(current_fen)
                    # Store for future use
                    st.session_state.analysis_results[current_fen] = eval_result
                    add_debug_info("Generated new analysis for current position")

                if "error" not in eval_result:
                    # Display evaluation
                    eval_type = eval_result["evaluation"]["type"]
                    eval_value = eval_result["evaluation"]["value"]

                    if eval_type == "cp":
                        # Convert centipawns to pawns
                        pawns = eval_value / 100.0
                        advantage = "White" if pawns > 0 else "Black"
                        st.markdown(f"**Evaluation:** {abs(pawns):.2f} pawns advantage for {advantage}")
                        add_debug_info(f"Displayed evaluation: {abs(pawns):.2f} pawns advantage for {advantage}")
                    elif eval_type == "mate":
                        advantage = "White" if eval_value > 0 else "Black"
                        st.markdown(f"**Evaluation:** Mate in {abs(eval_value)} for {advantage}")
                        add_debug_info(f"Displayed evaluation: Mate in {abs(eval_value)} for {advantage}")

                    # Display top moves
                    if "top_moves" in eval_result:
                        print(eval_result)
                        st.markdown("**Top Moves:**")
                        for i, move_info in enumerate(eval_result["top_moves"]):
                            st.markdown(f"{i+1}. {move_info['Move']}")
                        add_debug_info(f"Displayed {len(eval_result['top_moves'])} top moves")
                else:
                    st.error(f"Error in Stockfish analysis: {eval_result['error']}")
                    add_debug_info(f"Error in Stockfish analysis: {eval_result['error']}")
            # Display AI analysis
            if "ai_analysis" in st.session_state.game_info:
                st.subheader("Overall Game Analysis")
                st.markdown(st.session_state.game_info["ai_analysis"])
                add_debug_info("Displayed AI analysis")
            # Display game metadata if available
            if "metadata" in st.session_state.game_info:
                st.subheader("Game Information")
                metadata = st.session_state.game_info["metadata"]
                for key, value in metadata.items():
                    if key in ["White", "Black", "Date", "Event", "Site", "Result"]:
                        st.markdown(f"**{key}:** {value}")
                add_debug_info("Displayed game metadata")

        # Debug information (can be toggled)
        if st.checkbox("Show Debug Information"):
            st.subheader("Debug Information")
            debug_text = "\n".join(st.session_state.debug_info)
            st.markdown(f"<div class='debug-info'>{debug_text}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
