import unittest
from unittest.mock import patch, MagicMock
import sys

class TestAIService(unittest.TestCase):
    
    @patch('transformers.AutoTokenizer.from_pretrained')
    @patch('transformers.AutoModelForCausalLM.from_pretrained')
    @patch('transformers.pipeline')
    def test_init(self, mock_pipeline, mock_model, mock_tokenizer):
        # Setup mocks
        mock_tokenizer.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        mock_pipeline.return_value = MagicMock()
        
        # Import here to use the mocks
        from ai_service import AIService
        
        # Create service
        service = AIService()
        
        # Verify initialization
        self.assertTrue(service.model_available)
        mock_model.assert_called_once()
        mock_pipeline.assert_called_once()
    
    @patch('transformers.pipeline')
    def test_analyze_position(self, mock_pipeline):
        # Setup mock
        mock_pipe = MagicMock()
        mock_pipe.return_value = [{'generated_text': 'Test prompt\nAnalysis result'}]
        mock_pipeline.return_value = mock_pipe
        
        # Import with mocks
        from ai_service import AIService
        
        # Create service with mocked components
        with patch.object(AIService, '__init__', return_value=None):
            service = AIService()
            service.model_available = True
            service.pipe = mock_pipe
            
            # Test analyze_position
            result = service.analyze_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Verify result
            self.assertEqual(result, "Analysis result")
            mock_pipe.assert_called_once()
    
    @patch('transformers.pipeline')
    def test_analyze_game(self, mock_pipeline):
        # Setup mock
        mock_pipe = MagicMock()
        mock_pipe.return_value = [{'generated_text': 'Test prompt\nGame analysis result'}]
        mock_pipeline.return_value = mock_pipe
        
        # Import with mocks
        from ai_service import AIService
        
        # Create service with mocked components
        with patch.object(AIService, '__init__', return_value=None):
            service = AIService()
            service.model_available = True
            service.pipe = mock_pipe
            
            # Test analyze_game
            result = service.analyze_game("[Event \"Test Game\"]\n[Site \"?\"]\n[Date \"2023.01.01\"]\n[Round \"?\"]\n[White \"Player1\"]\n[Black \"Player2\"]\n[Result \"1-0\"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Na5 10. Bc2 c5 11. d4 Qc7 12. Nbd2 cxd4 13. cxd4 Nc6 14. Nb3 a5 15. Be3 a4 16. Nbd2 Bd7 17. Rc1 Qb8 18. d5 Na7 19. a3 Rc8 20. b4 axb3 21. Nxb3 Rxc1 22. Qxc1 Qa8 23. Qb2 Rc8 24. Bd3 Nc6 25. Rc1 Nb8 26. Rxc8+ Qxc8 27. Qc1 Qxc1+ 28. Bxc1 Na6 29. Be3 Kf8 30. Nd2 Ke8 31. f3 Kd8 32. Kf2 Kc7 33. Ke2 Kb6 34. Kd1 h6 35. Kc2 g5 36. Kb3 Nc7 37. a4 bxa4+ 38. Kxa4 Ne8 39. Kb3 f6 40. g4 Ng7 41. Nc4+ Kc7 42. Na5 Kb6 43. Nc4+ Kc7 44. Na5 Kb6 45. Nc4+ 1/2-1/2")
            
            # Verify result
            self.assertEqual(result, "Game analysis result")
            mock_pipe.assert_called_once()

if __name__ == '__main__':
    unittest.main()
