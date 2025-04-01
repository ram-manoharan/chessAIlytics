import os
import subprocess
import sys

def install_stockfish():
    """Install Stockfish chess engine if not already installed"""
    try:
        # Check if stockfish is already installed
        result = subprocess.run(['which', 'stockfish'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Stockfish is already installed at:", result.stdout.strip())
            return True
        
        # Install stockfish
        print("Installing Stockfish...")
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run(['apt-get', 'install', '-y', 'stockfish'], check=True)
        
        # Verify installation
        result = subprocess.run(['which', 'stockfish'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Stockfish installed successfully at:", result.stdout.strip())
            return True
        else:
            print("Failed to install Stockfish")
            return False
    except Exception as e:
        print(f"Error installing Stockfish: {str(e)}")
        return False

def setup_environment():
    """Setup the environment for the chess analyzer"""
    # Install required packages
    print("Installing required packages...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    
    # Install Stockfish
    install_stockfish()
    
    print("Environment setup complete")

if __name__ == "__main__":
    setup_environment()
