# Deployment Instructions

This document provides instructions for deploying the Chess Game Analyzer to Hugging Face Spaces and GitHub.

## GitHub Deployment

1. Create a new GitHub repository
2. Push the code to the repository:

```bash
# Initialize git repository
git init

# Add all files
git add .

# Commit changes
git commit -m "Initial commit"

# Add remote repository
git remote add origin https://github.com/username/chess-game-analyzer.git

# Push to GitHub
git push -u origin main
```

## Hugging Face Spaces Deployment

1. Go to [Hugging Face](https://huggingface.co/) and sign in or create an account
2. Click on your profile picture and select "New Space"
3. Choose "Streamlit" as the SDK
4. Fill in the Space name (e.g., "chess-game-analyzer")
5. Choose "Public" visibility
6. Click "Create Space"
7. In the "Files" tab, you can either:
   - Upload the files directly through the web interface
   - Connect your GitHub repository for automatic deployment

### Option 1: Direct Upload

Upload all the project files to your Hugging Face Space through the web interface.

### Option 2: GitHub Integration

1. In your Hugging Face Space, go to the "Settings" tab
2. Under "Repository", click "Connect to GitHub repository"
3. Select your GitHub repository
4. Configure the branch to deploy (usually "main")
5. Save the settings

The Space will automatically deploy from your GitHub repository whenever you push changes.

## Environment Setup on Hugging Face

Hugging Face Spaces will automatically:
1. Install dependencies from requirements.txt
2. Install Stockfish using the setup.py script
3. Run the Streamlit app specified in the Spacefile

## Troubleshooting

If you encounter issues with the deployment:

1. Check the build logs in the Hugging Face Space
2. Ensure all dependencies are correctly listed in requirements.txt
3. Verify that the Spacefile correctly points to app.py
4. Check that the DeepSeek-V3 model is accessible from Hugging Face
