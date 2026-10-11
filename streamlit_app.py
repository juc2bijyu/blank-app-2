import streamlit as st
import requests
import pandas as pd

st.title("📝 データ保存アプリ (GAS連携)")

# SecretsからGASのURLを取得
if "GAS_URL" not in st.secrets:
    st.error("Secrets に GAS_URL が設定されていません。")
    st.stop()

gas_url = st.secrets["GAS_URL"]

# データの読み込み関数
def load_data():
    try:
        response = requests.get(gas_url)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return []

# 1. ユーザー入力フォーム
with st.form("input_form", clear_on_submit=True):
    st.subheader("新しいデータを登録")
    name = st.text_input("お名前")
    content = st.text_area("内容・メッセージ")
    submitted = st.form_submit_button("スプレッドシートに保存")

    if submitted:
        if not name or not content:
            st.warning("お名前と内容の両方を入力してください。")
        else:
            payload = {
                "user_name": name,
                "content": content
            }
            with st.spinner("保存中..."):
                res = requests.post(gas_url, json=payload)
                if res.status_code == 200:
                    st.success("スプレッドシートに保存しました！")
                    st.rerun()  # 画面を再読み込みして最新データを反映
                else:
                    st.error("保存に失敗しました。")

# 2. 蓄積されたデータの表示
st.divider()
st.subheader("📊 保存済みデータ一覧")
data = load_data()

if data:
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
else:
    st.info("保存されたデータはまだありません。")
