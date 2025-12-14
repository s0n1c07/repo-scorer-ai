import streamlit as st
import requests
import json
from datetime import datetime
import google.generativeai as genai

# Configuration
st.set_page_config(
    page_title="Repo Scorer AI", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

GITHUB_API = "https://api.github.com"
GEMINI_KEY = st.secrets.get("gemini_key", None)

# Gemini Model Initialization
@st.cache_resource
def init_gemini(api_key):
    if not api_key:
        st.error("Gemini API Key not found in secrets.toml. Please configure it.")
        st.stop()
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"Error initializing Gemini: {e}")
        st.stop()

model = init_gemini(GEMINI_KEY)

# GitHub Data Fetching
def fetch_repo_data(owner, repo, token=None):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        repo_url = f"{GITHUB_API}/repos/{owner}/{repo}"
        repo_response = requests.get(repo_url, headers=headers, timeout=5)
        if repo_response.status_code != 200:
            message = repo_response.json().get('message', 'Unknown Error')
            return {"error": f"GitHub API failed: {repo_response.status_code} - {message}"}
        repo_data = repo_response.json()

        commits_url = f"{GITHUB_API}/repos/{owner}/{repo}/commits" # Fetch commits (top 50 for consistency metric)
        commits_data = requests.get(commits_url, headers=headers, params={"per_page": 50}, timeout=5).json()
        
        readme_url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/README.md" # Check for README.md existence
        readme = requests.head(readme_url, headers=headers, timeout=5)
        readme_text = "README exists and is accessible" if readme.status_code == 200 else "No README found"
        return {
            "name": repo_data.get("name"),
            "description": repo_data.get("description"),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "language": repo_data.get("language", "Unknown"),
            "url": repo_data.get("html_url"),
            "commits": len(commits_data) if isinstance(commits_data, list) else 0,
            "readme": readme_text,
            "topics": repo_data.get("topics", [])
        }
    except requests.exceptions.Timeout:
        return {"error": "Request to GitHub timed out."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

# AI Prompt Generation and Call
def get_ai_analysis(repo_data):
    data_for_prompt = {
        "name": repo_data.get('name', 'N/A'),
        "description": repo_data.get('description', 'N/A'),
        "stars": repo_data.get('stars', 0),
        "forks": repo_data.get('forks', 0),
        "language": repo_data.get('language', 'Unknown'),
        "commits": repo_data.get('commits', 0),
        "readme": repo_data.get('readme', 'N/A'),
        "topics": ', '.join(repo_data.get('topics', [])) if repo_data.get('topics') else 'None'
    }

    prompt = f"""You are an AI Coding Mentor. Analyze this GitHub repository and provide a structured evaluation focused on giving honest, actionable feedback.

Repository Data:
- Name: {data_for_prompt['name']}
- Description: {data_for_prompt['description']}
- Stars: {data_for_prompt['stars']}
- Forks: {data_for_prompt['forks']}
- Language: {data_for_prompt['language']}
- Total Commits (from last 50): {data_for_prompt['commits']}
- README Status: {data_for_prompt['readme']}
- Topics: {data_for_prompt['topics']}

Provide a JSON response with exactly this structure:
{{
    "score": <0-100 integer>,
    "level": "<Beginner/Intermediate/Advanced>",
    "medal": "<Bronze/Silver/Gold>",
    "summary": "<2-3 sentences of honest feedback on the project's current quality, structure, and potential.>",
    "strengths": ["<strength1>", "<strength2>", "<strength3>"],
    "improvements": ["<improvement1>", "<improvement2>", "<improvement3>"],
    "roadmap": ["<Actionable Step 1, e.g., Add unit tests>", "<Actionable Step 2, e.g., Improve folder structure>", "<Actionable Step 3, e.g., Commit regularly>"]
}}

Be critical but fair. Score based on code quality, documentation, popularity, activity, and practical usefulness. The 'roadmap' array MUST provide 3-5 specific, actionable steps the student can immediately follow to improve the project's grade, focusing on documentation, testing, and Git best practices."""

    response = model.generate_content(prompt)
    response_text = response.text.strip()
    try:
        if response_text.startswith("```json"):
             response_text = response_text.replace("```json", "", 1).rstrip("`").strip()
        elif response_text.startswith("```"):
             response_text = response_text.replace("```", "", 1).rstrip("`").strip()
        
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        st.error("Failed to parse AI response. The model may have returned invalid JSON.")
        st.code(response_text)
        return {"error": "Invalid AI response format."}

# Streamlit App Layout
def main():
    st.title("🥇 Repo Scorer AI")
    st.markdown("## GitGrade Hackathon: Repository Mirror")
    st.caption("Automated GitHub Repository Analysis powered by Gemini 2.5 Flash.")
    st.divider()

    repo_url = st.text_input(
        "Enter GitHub Repository URL",
        placeholder="e.g., https://github.com/owner/repo",
        key="repo_url_input"
    )
    
    if st.button("🚀 Analyze Repository", use_container_width=True, type="primary"):
        if not repo_url:
            st.error("Please enter a repository URL.")
            return

        if 'last_analyzed_url' in st.session_state and st.session_state.last_analyzed_url == repo_url:
             st.info("Repository already analyzed. Please enter a new URL or refresh the page to re-analyze.")
             return

        with st.spinner("🔄 Fetching data and analyzing repository..."):
            try:
                url_parts = repo_url.strip().rstrip('/').split('/')
                if len(url_parts) < 2 or url_parts[-2] == "" or url_parts[-1] == "":
                    st.error("Invalid repository URL format. Please use the full URL.")
                    return
                    
                owner = url_parts[-2]
                repo = url_parts[-1]

                repo_data = fetch_repo_data(owner, repo)
                
                if "error" in repo_data:
                    st.error(f"Error fetching repository data: {repo_data['error']}")
                    return

                result = get_ai_analysis(repo_data)
                
                if "error" in result:
                    return

                st.session_state.last_analyzed_url = repo_url # Store URL to prevent double-analysis
                st.balloons()
                st.success("Analysis Complete!")
                
                # Display Results
                
                # 1. Scorecard Section
                st.header(f"Evaluation for **{repo_data['name']}**")
                
                medal_map = {"Gold": "🥇", "Silver": "🥈", "Bronze": "🥉"}
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Score", f"{result.get('score', 0)}/100")
                
                with col2:
                    st.metric("Level", result.get('level', 'Unknown'))
                
                with col3:
                    st.metric("Medal", f"{medal_map.get(result.get('medal', 'Bronze'), '⭐')} {result.get('medal', 'Bronze')}")
                
                with col4:
                    st.metric("Language", repo_data.get('language', 'Unknown'))

                st.divider()
                
                # 2. Roadmap
                st.subheader("💡 Personalized Roadmap: Your Next Steps")
                st.markdown("**This is your guidance from an AI coding mentor.**")
                
                roadmap_steps = result.get('roadmap', [])
                if roadmap_steps:
                    for i, step in enumerate(roadmap_steps):
                        st.write(f"**{i+1}.** {step}")
                else:
                    st.info("The AI did not generate specific roadmap steps.")

                st.divider()

                # Summary and Feedback
                st.subheader("📋 Summary & Feedback")
                st.info(result.get('summary', 'No summary available.'))
                st.markdown(f"🔗 [View on GitHub]({repo_data['url']}) | Topics: **{', '.join(repo_data.get('topics', [])) or 'None'}**")
                
                st.divider()

                # 3. Detailed Strengths and Improvements
                st.subheader("Detailed Strengths and Improvements")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### ✅ Strengths")
                    for strength in result.get('strengths', []):
                        st.success(f"• {strength}")
                
                with col2:
                    st.markdown("#### 🎯 Areas to Improve")
                    for improvement in result.get('improvements', []):
                        st.warning(f"• {improvement}")
                
                st.divider()
                
                st.caption(f"Analysis performed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            except Exception as e:
                st.error(f"An unexpected error occurred during analysis: {str(e)}")

if __name__ == "__main__":
    main()