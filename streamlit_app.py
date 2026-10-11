import streamlit as st
import requests
import pandas as pd
import re

st.set_page_config(page_title="タスク・〆切管理", layout="wide")
st.title("📋 タスク・〆切管理アプリ")

if "GAS_URL" not in st.secrets:
    st.error("Secrets に GAS_URL が設定されていません。")
    st.stop()

gas_url = st.secrets["GAS_URL"]

# 時刻文字列の整形関数
def format_to_hh_mm(val):
    if pd.isna(val) or val is None or str(val).strip() == "":
        return ""
    val_str = str(val).strip()
    match = re.search(r"(\d{1,2}):(\d{2})", val_str)
    if match:
        h, m = match.groups()
        return f"{int(h):02d}:{m}"
    return val_str

# データの読み込み
def load_data():
    try:
        response = requests.get(gas_url, allow_redirects=True)
        if response.status_code == 200:
            if not response.text.strip():
                return pd.DataFrame()
            raw_data = response.json()
            if not raw_data or not isinstance(raw_data, list):
                return pd.DataFrame()
            
            df = pd.DataFrame(raw_data)
            
            # 列名のマッピング（大文字小文字・日本語混在を吸収）
            col_map = {}
            for col in df.columns:
                c_clean = str(col).strip()
                if c_clean.lower() == "id":
                    col_map[col] = "ID"
                elif c_clean in ["曜日", "day_of_week"]:
                    col_map[col] = "曜日"
                elif c_clean in ["〆切時刻", "締切時刻", "deadline_time"]:
                    col_map[col] = "〆切時刻"
                elif c_clean in ["内容", "content"]:
                    col_map[col] = "内容"
            
            df = df.rename(columns=col_map)
            
            # 〆切時刻を HH:MM 形式に統一
            if "〆切時刻" in df.columns:
                df["〆切時刻"] = df["〆切時刻"].apply(format_to_hh_mm)
            
            # IDを正しく整数型に変換
            if "ID" in df.columns:
                df["ID"] = pd.to_numeric(df["ID"], errors="coerce").fillna(0).astype(int)
            
            target_cols = [c for c in ["ID", "曜日", "〆切時刻", "内容"] if c in df.columns]
            return df[target_cols]
        else:
            st.error(f"ステータスコードエラー: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

# -------------------------------------------------------------
# 1行配置フォーム
# -------------------------------------------------------------
with st.form("quick_input_form", clear_on_submit=True):
    col_day, col_time, col_content, col_btn = st.columns(
        [1.2, 1.3, 4.5, 1.0], 
        vertical_alignment="bottom"
    )
    
    with col_day:
        day_input = st.text_input("曜日", placeholder="例: 木曜日")
        
    with col_time:
        time_input = st.text_input("〆切時刻", placeholder="例: 10:30")
        
    with col_content:
        content_input = st.text_input("内容", placeholder="例: 課題採点")
        
    with col_btn:
        submitted = st.form_submit_button("登録", use_container_width=True)

    if submitted:
        if not day_input or not time_input or not content_input:
            st.warning("すべての項目を入力してください。")
        else:
            formatted_time = format_to_hh_mm(time_input)
            
            # スプレッドシート側のヘッダー（日本語・英語どちらでも届くように設定）
            payload = {
                "day_of_week": day_input,
                "deadline_time": formatted_time,
                "content": content_input,
                "曜日": day_input,
                "〆切時刻": formatted_time,
                "内容": content_input
            }
            
            with st.spinner("保存中..."):
                res = requests.post(gas_url, json=payload)
                if res.status_code == 200:
                    st.success("追加しました！")
                    st.rerun()
                else:
                    st.error("保存に失敗しました。")

# -------------------------------------------------------------
# 一覧表示
# -------------------------------------------------------------
st.divider()
st.subheader("📌 登録済み一覧")
df_data = load_data()

if not df_data.empty:
    st.dataframe(df_data, use_container_width=True, hide_index=True)
else:
    st.info("登録済みのデータはありません。")
