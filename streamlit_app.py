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
                elif c_clean in ["終了", "status"]:
                    col_map[col] = "終了"
                elif c_clean in ["毎週 / 単発", "毎週/単発", "recurrence"]:
                    col_map[col] = "種別"
                elif c_clean in ["日付", "date"]:
                    col_map[col] = "日付"
            
            df = df.rename(columns=col_map)
            
            if "〆切時刻" in df.columns:
                df["〆切時刻"] = df["〆切時刻"].apply(format_to_hh_mm)
            
            if "ID" in df.columns:
                df["ID"] = pd.to_numeric(df["ID"], errors="coerce").fillna(0).astype(int)
            
            # E列「終了」が "OK" なら True に変換
            if "終了" in df.columns:
                df["完了"] = df["終了"].str.strip() == "OK"
            else:
                df["完了"] = False
            
            # 日付列が存在しない場合は空文字で作成
            if "日付" not in df.columns:
                df["日付"] = ""
            
            # 列の表示順: [完了, 日付, ID, 曜日, 〆切時刻, 内容, 種別]
            cols = ["完了", "日付", "ID", "曜日", "〆切時刻", "内容", "種別"]
            target_cols = [c for c in cols if c in df.columns]
            return df[target_cols]
        else:
            st.error(f"ステータスコードエラー: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

# -------------------------------------------------------------
# 1行配置フォーム（日付入力はなし）
# -------------------------------------------------------------
with st.form("quick_input_form", clear_on_submit=True):
    col_day, col_time, col_content, col_type, col_btn = st.columns(
        [1.1, 1.2, 4.0, 1.3, 1.0], 
        vertical_alignment="bottom"
    )
    
    with col_day:
        day_input = st.text_input("曜日", placeholder="例: 木曜日")
        
    with col_time:
        time_input = st.text_input("〆切時刻", placeholder="例: 10:30")
        
    with col_content:
        content_input = st.text_input("内容", placeholder="例: 課題採点")

    with col_type:
        type_input = st.selectbox("種別", ["毎週", "単発"], index=0)
        
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
                "content": content_input,
                "recurrence": type_input
            }
            with st.spinner("保存中..."):
                res = requests.post(gas_url, json=payload)
                if res.status_code == 200:
                    st.success("追加しました！")
                    st.rerun()
                else:
                    st.error("保存に失敗しました。")

# -------------------------------------------------------------
# 一覧表示（IDの左に日付を表示）
# -------------------------------------------------------------
st.divider()
st.subheader("📌 登録済み一覧")
df_data = load_data()

if not df_data.empty:
    edited_df = st.data_editor(
        df_data,
        hide_index=True,
        disabled=["日付", "ID", "曜日", "〆切時刻", "内容", "種別"],
        use_container_width=True,
        key="task_editor"
    )

    # チェックボックスの変更を検知してGASへ送信
    editor_state = st.session_state.get("task_editor", {})
    edited_rows = editor_state.get("edited_rows", {})

    if edited_rows:
        for row_index, changes in edited_rows.items():
            if "完了" in changes:
                target_id = int(df_data.iloc[row_index]["ID"])
                is_done = changes["完了"]
                new_status = "OK" if is_done else ""
                
                update_payload = {
                    "action": "update_status",
                    "id": target_id,
                    "status": new_status
                }
                
                with st.spinner("更新中..."):
                    requests.post(gas_url, json=update_payload)
                
                st.rerun()
else:
    st.info("登録済みのデータはありません。")
