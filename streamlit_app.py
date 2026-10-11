import streamlit as st
import requests
import pandas as pd
import re

# 画面を広く使う設定
st.set_page_config(page_title="タスク・〆切管理", layout="wide")

st.title("📋 タスク・〆切管理アプリ")

# SecretsからGASのURLを取得
if "GAS_URL" not in st.secrets:
    st.error("Secrets に GAS_URL が設定されていません。")
    st.stop()

gas_url = st.secrets["GAS_URL"]

# 時刻文字列を "10:30" 形式に正規化する関数
def format_to_hh_mm(val):
    if pd.isna(val) or val is None or str(val).strip() == "":
        return ""
    val_str = str(val).strip()
    match = re.search(r"(\d{1,2}):(\d{2})", val_str)
    if match:
        h, m = match.groups()
        return f"{int(h):02d}:{m}"
    return val_str

# データの読み込み関数
def load_data():
    try:
        response = requests.get(gas_url)
        if response.status_code == 200:
            raw_data = response.json()
            if not raw_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(raw_data)
            
            # 〆切時刻の列が存在する場合、"10:30" 形式に一括変換
            if "deadline_time" in df.columns:
                df["deadline_time"] = df["deadline_time"].apply(format_to_hh_mm)
            
            # 日本語列名へのリネーム
            rename_map = {
                "id": "ID",
                "day_of_week": "曜日",
                "deadline_time": "〆切時刻",
                "content": "内容"
            }
            df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
            
            # 列の並び順を明示（IDを先頭に配置）
            cols_order = [c for c in ["ID", "曜日", "〆切時刻", "内容"] if c in df.columns]
            return df[cols_order]
        return pd.DataFrame()
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

# -------------------------------------------------------------
# 1行にコンパクトに配置した入力フォーム
# -------------------------------------------------------------
with st.form("quick_input_form", clear_on_submit=True):
    col_day, col_time, col_content, col_btn = st.columns(
        [1.2, 1.3, 4.5, 1.0], 
        vertical_alignment="bottom"
    )
    
    with col_day:
        day_input = st.text_input("曜日", placeholder="例: 月")
        
    with col_time:
        time_input = st.text_input("〆切時刻", placeholder="例: 10:30")
        
    with col_content:
        content_input = st.text_input("内容", placeholder="例: 第3回 課題レポート提出")
        
    with col_btn:
        submitted = st.form_submit_button("登録", use_container_width=True)

    if submitted:
        if not day_input or not time_input or not content_input:
            st.warning("すべての項目を入力してください。")
        else:
            formatted_time = format_to_hh_mm(time_input)
            
            payload = {
                "day_of_week": day_input,
                "deadline_time": formatted_time,
                "content": content_input
            }
            
            with st.spinner("保存中..."):
                res = requests.post(gas_url, json=payload)
                if res.status_code == 200:
                    st.success("追加しました！")
                    st.rerun()
                else:
                    st.error("保存に失敗しました。")

# -------------------------------------------------------------
# 保存済みデータの一覧表示
# -------------------------------------------------------------
st.divider()
st.subheader("📌 登録済み一覧")
df_data = load_data()

if not df_data.empty:
    st.dataframe(df_data, use_container_width=True, hide_index=True)
else:
    st.info("登録済みのデータはありません。")
