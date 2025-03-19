import streamlit as st
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

# --- ページ設定（タイトル変更） ---
st.set_page_config(page_title="村上事務所についてのBOT", page_icon="🏢", layout="wide")
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# --- タイトル表示 ---
st.title("🏢 村上事務所についてのBOT")

# --- 環境変数読み込み ---
load_dotenv()
API_KEY = os.getenv("API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={API_KEY}"

# --- 対象URL ---
TARGET_URL = "https://murakami.tax/"

# --- URLからテキスト取得 ---
def fetch_text_from_url(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        return soup.get_text()
    except Exception as e:
        return f"❌ URLの読み込みエラー: {e}"

# --- Geminiへの質問 ---
def ask_gemini(text, question):
    prompt = f"""
以下のWebサイトの内容をもとに、質問に「やさしい言葉」で答えてください。
・必要があれば「箇条書き」でまとめてください。
・専門用語はできるだけ使わず、わかりやすい表現にしてください。

【Webサイトの内容】
{text[:4000]}

【質問】
{question}
"""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(GEMINI_URL, json=payload)
    if res.status_code == 200:
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"❌ エラー: {res.status_code} - {res.text}"

# --- 状態管理 ---
if "question" not in st.session_state:
    st.session_state.question = ""
if "answer" not in st.session_state:
    st.session_state.answer = ""

# --- 入力フォーム ---
with st.form("qa_form"):
    st.session_state.question = st.text_input("質問を入力してください", value=st.session_state.question)
    submitted = st.form_submit_button("💬 質問する")

# --- 本文取得 ---
text = fetch_text_from_url(TARGET_URL)

# --- 回答処理 ---
if submitted and st.session_state.question:
    with st.spinner("⌛ 回答を準備しています..."):
        st.session_state.answer = ask_gemini(text, st.session_state.question)

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