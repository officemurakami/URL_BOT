import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import os

# --- ページ設定 ---
st.set_page_config(page_title="村上事務所についてのBOT", page_icon="🏢", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🏢 村上事務所についてのBOT")

# --- 環境変数 ---
load_dotenv()
API_KEY = os.getenv("API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={API_KEY}"

# --- 対象URL ---
BASE_URL = "https://murakami.tax/"

# --- サイト内リンク取得 ---
def get_all_links(url, base_domain):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = set()
        for a in soup.find_all("a", href=True):
            link = urljoin(url, a["href"])
            parsed = urlparse(link)
            if parsed.netloc == base_domain:
                clean_link = parsed.scheme + "://" + parsed.netloc + parsed.path
                links.add(clean_link)
        return links
    except Exception as e:
        return set()

# --- 全ページのテキスト取得（再帰） ---
def crawl_site_texts(base_url, max_depth=2):
    visited = set()
    to_visit = {base_url}
    base_domain = urlparse(base_url).netloc
    all_text = ""

    for depth in range(max_depth):
        next_visit = set()
        for url in to_visit:
            if url in visited:
                continue
            try:
                res = requests.get(url, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")
                page_text = soup.get_text(separator=" ", strip=True)
                all_text += page_text + "\n\n"
                visited.add(url)
                next_visit.update(get_all_links(url, base_domain))
            except Exception:
                continue
        to_visit = next_visit - visited
    return all_text

# --- Geminiへの質問 ---
def ask_gemini(text, question):
    prompt = f"""
以下のWebサイトの内容をもとに、質問に「やさしい言葉」で答えてください。
・必要があれば「箇条書き」でまとめてください。
・専門用語はできるだけ使わず、わかりやすい表現にしてください。

【Webサイトの内容】
{text[:12000]}

【質問】
{question}
"""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(GEMINI_URL, json=payload)
    if res.status_code == 200:
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"❌ エラー: {res.status_code} - {res.text}"

# --- セッション管理 ---
if "question" not in st.session_state:
    st.session_state.question = ""
if "answer" not in st.session_state:
    st.session_state.answer = ""

# --- フォーム ---
with st.form("qa_form"):
    st.session_state.question = st.text_input("質問を入力してください", value=st.session_state.question)
    submitted = st.form_submit_button("💬 質問する")

# --- テキスト取得 ---
with st.spinner("🔍 サイト全体を読み込んでいます..."):
    site_text = crawl_site_texts(BASE_URL)

# --- 回答 ---
if submitted and st.session_state.question:
    with st.spinner("⌛ 回答を準備しています..."):
        st.session_state.answer = ask_gemini(site_text, st.session_state.question)

# --- 表示 ---
if st.session_state.answer:
    st.markdown("### 回答：")
    st.write(st.session_state.answer)

# --- クリアボタン ---
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🧹 回答クリア"):
        st.session_state.question = ""
        st.session_state.answer = ""
