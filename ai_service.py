import os
from typing import List, Dict, Any, Optional
import groq
from groq import Groq
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Fetch API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
class AIService:
    """
    A service that uses Groq's LLaMA model for chess analysis.
    """
    
    def __init__(self):
        try:
            self.model_name = "llama3-70b-chat"  # Use the strongest LLaMA model available in Groq
            self.model_available = True
            self.client = Groq(api_key=GROQ_API_KEY)
        except Exception as e:
            self.model_available = False

    def analyze_position(self, fen: str) -> str:
        """
        Analyze a chess position given in FEN notation using Groq's API and a LLaMA model.

        Args:
            fen: The FEN string representing the chess position

        Returns:
            A string containing the analysis
        """ 
        if not self.model_available:
            return "LLaMA model not available"

        try:
            # Define the structured prompt
            prompt = f"""
            The following is a conversation with a chess grandmaster AI.

            User: Can you analyze this chess position given in FEN notation?
            {fen}

            Please provide:
            1. Overall assessment of the position (material, piece activity, king safety)
            2. Key tactical and strategic ideas for both sides
            3. 2-3 concrete best moves with brief explanations
            4. Any potential mistakes to avoid

            Grandmaster AI:
            """
            
            # Call Groq API
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Use the strongest available model
                messages=[{"role": "user", "content": prompt}],
            )

            return response.choices[0].message.content 
        
        except Exception as e:
            return f"Error in analysis: {str(e)}"
    
    def analyze_game(self, pgn_text: str, player_name: Optional[str] = None) -> str:
        """
        Analyze a complete chess game from PGN notation.

        Args:
            pgn_text: The PGN text of the chess game
            player_name: Optional name of the player to focus on

        Returns:
            A string containing the game analysis
        """
        if not self.model_available:
            return "LLaMA model not available"

        try:
            # Format the prompt as a conversation
            prompt = f"""
            The following is a conversation with a chess grandmaster AI.

            User: Can you analyze this chess game?
            {pgn_text}

            {f'Focus on player: {player_name}' if player_name else ''}

            Please provide:
            1. Opening identification and assessment
            2. Key turning points in the game
            3. Critical mistakes and missed opportunities
            4. Strategic themes throughout the game
            5. Suggestions for improvement

            Grandmaster AI:
            """

            # Call Groq API
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Use the strongest available model
                messages=[{"role": "user", "content": prompt}],
            )

            return response.choices[0].message.content 

        except Exception as e:
            return f"Error in analysis: {str(e)}"

