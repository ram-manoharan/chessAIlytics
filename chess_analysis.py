import os
import logging
import streamlit as st
from typing import Dict, Any, List, Optional
import re
from io import StringIO
import chess
import chess.pgn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the AI service and Visualization service
from ai_service import AIService
from visualization_service import VisualizationService

# Debug info list for tracking application flow
debug_info = []

def add_debug_info(message):
    """Add a debug message to the global debug info list"""
    global debug_info
    debug_info.append(message)
    logger.info(message)

# Stockfish Service
class StockfishService:
    def __init__(self, stockfish_path=None, depth=18):
        try:
            import chess.engine
            os.chmod("./stockfish_14_x64_popcnt",0o0777)
            self.engine = chess.engine.SimpleEngine.popen_uci(
               "./stockfish_14_x64_popcnt" 
            )
            self.engine.configure({"Threads": 2, "Hash": 128})
            self.depth = depth
            self.available = True
            add_debug_info("Stockfish engine initialized successfully")
        except Exception as e:
            add_debug_info(f"Failed to initialize Stockfish engine: {str(e)}")
            self.available = False
            self.engine = None

    def analyze_position(self, fen, multi_pv=1):
        if not self.available or not self.engine:
            return {"error": "Stockfish engine not available"}

        try:
            board = chess.Board(fen)
            
            # Get engine evaluation
            info = self.engine.analyse(
                board, 
                chess.engine.Limit(depth=self.depth),
                multipv=multi_pv
            )
            
            # Process results
            result = {
                "fen": fen,
                "top_moves": []
            }
            
            for pv_info in info:
                score = pv_info["score"].relative
                
                # Handle mate scores
                if score.is_mate():
                    eval_type = "mate"
                    eval_value = score.mate()
                else:
                    eval_type = "cp"
                    eval_value = score.score()
                
                # For the first PV, set the main evaluation
                if len(result["top_moves"]) == 0:
                    result["evaluation"] = {
                        "type": eval_type,
                        "value": eval_value
                    }
                
                # Add move info
                move_info = {
                    "Move": pv_info["pv"][0].uci(),
                    "Evaluation": {
                        "type": eval_type,
                        "value": eval_value
                    },
                    "SAN": board.san(pv_info["pv"][0])
                }
                
                result["top_moves"].append(move_info)
            
            return result
            
        except Exception as e:
            add_debug_info(f"Error in Stockfish analysis: {str(e)}")
            return {"error": f"Analysis error: {str(e)}"}

    def __del__(self):
        if hasattr(self, 'engine') and self.engine:
            try:
                self.engine.quit()
            except:
                pass

# Opening Database Service
class OpeningDBService:
    def __init__(self):
        self.openings_db = {}
        try:
            # Load ECO codes
            self.load_eco_codes()
            self.available = True
            add_debug_info("Opening database initialized successfully")
        except Exception as e:
            add_debug_info(f"Failed to initialize opening database: {str(e)}")
            self.available = False

    def load_eco_codes(self):
        # This is a simplified version - in a real app, you'd load from a file
        self.openings_db = {
            "e4 e5 Nf3": {"name": "King's Pawn Game", "eco": "C40"},
            "e4 e5 Nf3 Nc6 Bb5": {"name": "Ruy Lopez", "eco": "C60"},
            "e4 c5": {"name": "Sicilian Defense", "eco": "B20"},
            "d4 d5": {"name": "Queen's Pawn Game", "eco": "D00"},
            "d4 Nf6 c4 g6": {"name": "King's Indian Defense", "eco": "E60"},
            # Add more openings as needed
        }

    def identify_opening(self, moves):
        if not self.available:
            return {"error": "Opening database not available"}
            
        try:
            # Convert moves to a standard format for lookup
            moves_str = " ".join(moves)
            
            # Look for the longest matching sequence
            best_match = None
            best_match_length = 0
            
            for opening_moves, opening_data in self.openings_db.items():
                if moves_str.startswith(opening_moves) and len(opening_moves) > best_match_length:
                    best_match = opening_data
                    best_match_length = len(opening_moves)
            
            if best_match:
                return {
                    "name": best_match["name"],
                    "eco": best_match["eco"]
                }
            else:
                return {"name": "Unknown Opening", "eco": ""}
                
        except Exception as e:
            add_debug_info(f"Error identifying opening: {str(e)}")
            return {"error": f"Opening identification error: {str(e)}"}

# Game Analysis Service
class GameAnalysisService:
    def __init__(self, stockfish_service, ai_service, opening_db_service):
        self.stockfish_service = stockfish_service
        self.ai_service = ai_service
        self.opening_db_service = opening_db_service

    def analyze_game(self, pgn_text, analysis_depth="standard"):
        try:
            # Check for FEN tag
            fen_match = re.search(r'\[FEN \"(.+?)\"\]', pgn_text)
            custom_fen = None
            if fen_match:
                custom_fen = fen_match.group(1)
                add_debug_info(f"Found FEN: {custom_fen}")

                # Fix castling rights if needed
                if "HAha" in custom_fen:
                    custom_fen = custom_fen.replace("HAha", "KQkq")
                    add_debug_info(f"Fixed castling rights in FEN: {custom_fen}")

            # Parse the game
            pgn = StringIO(pgn_text)
            game = chess.pgn.read_game(pgn)

            if not game:
                return {"error": "Invalid PGN format"}

            # Initialize a board with the starting position
            board = chess.Board(custom_fen) if custom_fen else chess.Board()

            # Extract headers
            headers = dict(game.headers)
            
            # Extract moves
            moves = []
            uci_moves = []
            positions = []
            
            # Add initial position
            positions.append(board.fen())
            
            # Process each move
            node = game
            while node.variations:
                next_node = node.variations[0]
                move = next_node.move
                
                # Add SAN and UCI notation
                san = board.san(move)
                uci = move.uci()
                
                moves.append(san)
                uci_moves.append(uci)
                
                # Make the move on our board
                board.push(move)
                
                # Add the new position
                positions.append(board.fen())
                
                # Move to the next node
                node = next_node
            
            # Identify opening
            opening_info = self.opening_db_service.identify_opening(moves[:10])
            
            # Analyze key positions
            position_analyses = {}
            
            # Determine which positions to analyze based on depth
            positions_to_analyze = []
            
            if analysis_depth == "minimal":
                # Just analyze the final position
                positions_to_analyze = [positions[-1]]
            elif analysis_depth == "standard":
                # Analyze every 5th position plus the final position
                positions_to_analyze = [positions[i] for i in range(0, len(positions), 5)]
                if positions[-1] not in positions_to_analyze:
                    positions_to_analyze.append(positions[-1])
            elif analysis_depth == "deep":
                # Analyze every position
                positions_to_analyze = positions
            
            # Limit to a reasonable number to avoid overloading
            max_positions = 10
            if len(positions_to_analyze) > max_positions:
                # Always include first, last, and evenly spaced positions
                positions_to_analyze = [positions_to_analyze[0]] + \
                                      [positions_to_analyze[i] for i in range(1, len(positions_to_analyze)-1, 
                                                                            len(positions_to_analyze)//max_positions)] + \
                                      [positions_to_analyze[-1]]
            
            # Analyze selected positions
            for fen in positions_to_analyze:
                try:
                    #stockfish_analysis = self.stockfish_service.analyze_position(fen)
                    stockfish_analysis = self.ai_service.analyze_position(fen)
                    position_analyses[fen] = stockfish_analysis
                except Exception as e:
                    add_debug_info(f"Error analyzing position {fen}: {str(e)}")
            
            # Get AI analysis for the whole game if AI model is available
            if self.ai_service.model_available:
                ai_analysis = self.ai_service.analyze_game(pgn_text)
            else:
                ai_analysis = "AI model not available. AI analysis unavailable."
            
            # Compile results
            result = {
                "headers": headers,
                "moves": moves,
                "uci_moves": uci_moves,
                "positions": positions,
                "opening": opening_info,
                "position_analyses": position_analyses,
                "ai_analysis": ai_analysis
            }
            
            return result
            
        except Exception as e:
            add_debug_info(f"Error in game analysis: {str(e)}")
            return {"error": f"Analysis error: {str(e)}"}

# Initialize services
def initialize_services():
    stockfish_service = StockfishService()
    ai_service = AIService()
    opening_db_service = OpeningDBService()
    visualization_service = VisualizationService()
    
    game_analysis_service = GameAnalysisService(stockfish_service, ai_service, opening_db_service)
    
    return {
        "stockfish_service": stockfish_service,
        "ai_service": ai_service,
        "opening_db_service": opening_db_service,
        "visualization_service": visualization_service,
        "game_analysis_service": game_analysis_service
    }

# Background analysis function
def analyze_game_in_background(pgn_text, analysis_depth, services):
    try:
        logger.info("Starting background analysis...")
        # Perform analysis
        result = services["game_analysis_service"].analyze_game(
            pgn_text,
            analysis_depth
        )

        logger.info("Background analysis completed successfully")
        # Return result
        return result
    except Exception as e:
        logger.error(f"Error in background analysis: {str(e)}")
        return {"error": str(e)}
