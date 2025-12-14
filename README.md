### 🏆 REPO SCORER AI
This project is built to evaluate and provide actionable feedback on student GitHub repositories.

## 🌟 Project Goal
The primary goal of the Repo Scorer AI is to act as a "Repository Mirror", providing students with an honest reflection of their GitHub projects. It converts a raw GitHub repository URL into three key, meaningful outputs: a Score, a Written Summary, and a Personalized Roadmap. This system helps developers understand how their code quality, documentation, and development practices look to recruiters or mentors.

## 🛠️ Architecture and Approach
This system is built as a powerful Streamlit application, leveraging the strengths of the GitHub API for data collection and the Gemini model for sophisticated qualitative analysis.

# 1. Data Collection (GitHub API)
The application uses the requests library to interface directly with the public GitHub API to gather objective, quantifiable metrics for the analysis prompt, relying on unauthenticated (public) rate limits:

Repository Metrics: Stars, Forks, Primary Language.

Activity: Total commits (based on the last 50) to gauge development consistency.

Documentation: Status of the README.md file.

Topics/Tech Stack: List of repository topics.

# 2. AI Core (Gemini 2.5 Flash)
The Gemini model serves as the intelligence core, processing the raw data to provide structured, actionable feedback.

Role: The AI is instructed to function as an "AI Coding Mentor".

Structured Output: The model is strictly prompted to return a pure JSON object that is parsed by the Streamlit application.

Evaluation Dimensions: The AI judges the repository across multiple dimensions, including Code quality & readability, Project structure, Documentation & clarity, and Real-world relevance.

## ✨ Key Submission Outputs
The system generates the three required key outputs:

| Output Dimension | Example Format | Problem Statement Requirement |
|------------------|----------------|--------------------------------|
| **A. Score / Rating** | 91/100, Advanced, Gold | Provides a clear rating across numerical, level, and medal formats. |
| **B. Written Summary** | “Excellent project depth and clean codebase.” | A short evaluation describing the repository’s current quality. |
| **C. Personalized Roadmap** | “Add automated tests”, “Improve issue tracking” | Actionable steps the student must follow for improvement. |

## 💻 Local Setup Instructions
Follow these steps to run the application on your local machine.

# 1. Prerequisites
You must have Python 3.8+ installed.

# 2. Clone the Repository
```Bash
git clone [YOUR_GITHUB_REPO_URL]
cd REPO-SCORER-AI
```

# 3. Set up the Environment
Create a virtual environment and install the required libraries (as listed in requirements.txt):
```Bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# or .\venv\Scripts\activate.ps1 on Windows PowerShell
pip install -r requirements.txt
```

# 4. Configure Secrets (Gemini API Key Only)
The application requires only the Gemini API Key. For security, this must be stored in a secrets.toml file, which is excluded from the public repository via .gitignore.

Create a folder named .streamlit in the root of your project directory.

Inside .streamlit, create a file named secrets.toml.

Add your key to secrets.toml in the following exact format:

```Ini, TOML
# .streamlit/secrets.toml
gemini_key = "YOUR_GEMINI_API_KEY_HERE"
```

# 5. Run the Application
Start the Streamlit application from your terminal:

```Bash
streamlit run app.py
```
The app will open in your browser, ready for analysis!
