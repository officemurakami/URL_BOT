import streamlit as st
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

# --- ページ設定 ---
st.set_page_config(page_title="URLから答えるBOT", page_icon="🌐", layout="wide")
st.title("🌐 URLから答えるBOT")

# --- 環境変数読み込み ---
load_dotenv()
API_KEY = os.getenv("API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={API_KEY}"

# --- 固定URL（murakami.tax）---
TARGET_URL = "https://murakami.tax/"

# --- URLからテキスト抽出 ---
def fetch_text_from_url(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        return soup.get_text()
    except Exception as e:
        return f"❌ URLの読み込みエラー: {e}"

# --- Geminiで回答生成 ---
def ask_gemini(text, question):
    prompt = f"""
以下のWebページの内容を参考に、質問に対して「やさしい言葉」で説明してください。
分かりやすくするために、必要があれば「箇条書き」を使ってもOKです。

● 難しい専門用語は使わず、やさしい言い回しにしてください。
● 知識のない人にも伝わるように工夫してください。

【Webページの内容】
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

# --- Webページテキスト取得 ---
text = fetch_text_from_url(TARGET_URL)

if "❌" in text:
    st.error(text)
else:
    # --- 入力フォーム ---
    with st.form("form"):
        question = st.text_input("質問を入力してください")
        submitted = st.form_submit_button("💬 質問する")
        if submitted and question:
            with st.spinner("⌛ やさしい回答を準備中..."):
                answer = ask_gemini(text, question)
                st.markdown("### 回答：")
                st.write(answer)
