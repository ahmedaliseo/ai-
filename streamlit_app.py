# streamlit_app.py
import streamlit as st
import time
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from protego import Protego

# --- Bot User Agents ---
USER_AGENTS = {
    'OpenAI': {
        'OAI-SearchBot': 'OAI-SearchBot/1.0; +https://openai.com/searchbot',
        'ChatGPT-User': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot',
        'GPTBot': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.1; +https://openai.com/gptbot'
    },
    'Anthropic': {
        'ClaudeBot': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)',
        'Claude-User': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude-User/1.0; +Claude-User@anthropic.com)'
    },
    'Perplexity': {
        'PerplexityBot': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)',
        'Perplexity-User': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Perplexity-User/1.0; +https://perplexity.ai/perplexity-user)'
    }
}

# --- Helper Functions ---
def validate_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and parsed.netloc
    except Exception:
        return False

def get_robots_parser(url):
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        response = requests.get(robots_url, timeout=10)
        if response.status_code == 200:
            return Protego.parse(response.text)
        return None
    except Exception:
        return None

def check_robots_permission(robots_parser, user_agent, url):
    if not robots_parser:
        return True  # No robots.txt means allowed
    try:
        return robots_parser.can_fetch(url, user_agent)
    except Exception:
        return False

def parse_html(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else 'No title'
        robots_tag = soup.find('meta', attrs={'name': 'robots'})
        robots_content = robots_tag.get('content', '').strip() if robots_tag else ''
        if not robots_content:
            robots_meta = 'No robots meta'
            has_noindex = False
        else:
            robots_meta = robots_content
            has_noindex = 'noindex' in robots_content.lower()
        return title, robots_meta, has_noindex
    except Exception:
        return 'Parse error', 'Parse error', False

def crawl_with_user_agents(url):
    results = []
    robots_parser = get_robots_parser(url)
    for company, agents in USER_AGENTS.items():
        for bot_name, user_agent in agents.items():
            try:
                robots_allowed = check_robots_permission(robots_parser, user_agent, url)
                headers = {'User-Agent': user_agent}
                start_time = time.time()
                response = requests.get(url, headers=headers, timeout=30)
                load_time = time.time() - start_time
                title, robots_meta, has_noindex = parse_html(response.text)
                is_allowed = (response.status_code == 200 and robots_allowed and not has_noindex)
                results.append({
                    "Company": company,
                    "Bot Name": bot_name,
                    "Access": "✅ Allowed" if is_allowed else "❌ BLOCKED",
                    "Status Code": response.status_code,
                    "Robots Meta": robots_meta,
                    "Robots.txt": "Allowed" if robots_allowed else "Blocked",
                    "Title": title,
                    "Load Time": f"{load_time:.2f}s"
                })
            except requests.exceptions.RequestException as e:
                robots_allowed = check_robots_permission(robots_parser, user_agent, url)
                results.append({
                    "Company": company,
                    "Bot Name": bot_name,
                    "Access": "⚠️ Error",
                    "Status Code": "-",
                    "Robots Meta": str(e),
                    "Robots.txt": "Allowed" if robots_allowed else "Blocked",
                    "Title": "-",
                    "Load Time": "-"
                })
    return results

# --- Streamlit UI ---
st.set_page_config(page_title="AI Bots Checker", layout="wide")
st.title("🤖 AI Bots Accessibility Checker")

url = st.text_input("Enter website URL (with http/https):", "https://example.com")

if st.button("Run Check", key="run_check_button"):
    if not validate_url(url):
        st.error("Invalid URL. Please enter a valid one starting with http:// or https://")
    else:
        with st.spinner("Checking bots access..."):
            data = crawl_with_user_agents(url)
        st.success("Done!")
        st.dataframe(data)
