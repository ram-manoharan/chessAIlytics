import unittest
from unittest.mock import patch, MagicMock

class TestAIService(unittest.TestCase):
    
    def test_service_structure(self):
        """Test that the service has the correct structure and methods"""
        from AI_service import AIService
        
        # Create service without initialization
        service = AIService.__new__(AIService)
        
        # Check that the class has the required methods
        self.assertTrue(hasattr(service, 'analyze_position'))
        self.assertTrue(hasattr(service, 'analyze_game'))
        
        # Check method signatures
        import inspect
        analyze_position_sig = inspect.signature(service.analyze_position)
        self.assertIn('fen', analyze_position_sig.parameters)
        
        analyze_game_sig = inspect.signature(service.analyze_game)
        self.assertIn('pgn_text', analyze_game_sig.parameters)
        self.assertIn('player_name', analyze_game_sig.parameters)

if __name__ == '__main__':
    unittest.main()
