import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd

# APIのベースURL
API_URL = "http://localhost:8000"

# 管理者アカウントの設定
ADMIN_EMAIL = "u879269j@gmail.com"  # 変更してご利用ください
ADMIN_PASSWORD = "19901214"        # 変更してご利用ください
ADMIN_NAME = "システム管理者"
ADMIN_PHONE = "08049829107"

# 管理者アカウントが存在するか確認し、なければ作成する関数
def ensure_admin_exists():
    try:
        # ログインを試みる
        response = requests.post(
            f"{API_URL}/token",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        # ログイン成功 = アカウントが既に存在する
        if response.status_code == 200:
            st.sidebar.success("管理者アカウントが確認できました")
            return True
            
        # ログイン失敗 = アカウントが存在しない可能性
        else:
            # アカウント作成を試みる
            user_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "full_name": ADMIN_NAME,
                "phone_number": ADMIN_PHONE,
                "is_admin": True
            }
            
            create_response = requests.post(f"{API_URL}/register", json=user_data)
            
            if create_response.status_code == 200:
                st.sidebar.success("管理者アカウントを作成しました")
                return True
            else:
                st.sidebar.error(f"管理者アカウントの作成に失敗しました: {create_response.json()}")
                return False
                
    except Exception as e:
        st.sidebar.error(f"エラーが発生しました: {e}")
        return False

st.set_page_config(page_title="クリニック予約システム - 管理者", layout="wide")
st.title("クリニック予約システム - 管理者画面")

# セッション状態の初期化
if 'token' not in st.session_state:
    st.session_state.token = None
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'admin_checked' not in st.session_state:
    st.session_state.admin_checked = False

# 管理者アカウントのチェック（初回のみ）
if not st.session_state.admin_checked:
    ensure_admin_exists()
    st.session_state.admin_checked = True

# 管理者クレデンシャルを表示
with st.sidebar.expander("管理者ログイン情報"):
    st.write(f"メールアドレス: {ADMIN_EMAIL}")
    st.write(f"パスワード: {ADMIN_PASSWORD}")

# ログイン状態に応じて表示を切り替え
if not st.session_state.is_logged_in:
    st.header("ログイン")
    
    with st.form("login_form"):
        email = st.text_input("メールアドレス")
        password = st.text_input("パスワード", type="password")
        submit = st.form_submit_button("ログイン")
        
        if submit:
            try:
                response = requests.post(
                    f"{API_URL}/token",
                    data={"username": email, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data["access_token"]
                    
                    # ユーザー情報を取得
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    user_response = requests.get(f"{API_URL}/users/me", headers=headers)
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        if user_data.get("is_admin", False):
                            st.session_state.is_logged_in = True
                            st.session_state.user_data = user_data
                            st.rerun()
                        else:
                            st.error("管理者権限がありません")
                    else:
                        st.error("ユーザー情報の取得に失敗しました")
                else:
                    st.error("ログインに失敗しました。メールアドレスまたはパスワードが間違っています。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

    # 管理者アカウント作成フォーム（実際の運用では削除してください）
    with st.expander("管理者アカウント作成（開発用）"):
        with st.form("register_form"):
            reg_email = st.text_input("メールアドレス")
            reg_password = st.text_input("パスワード", type="password")
            reg_name = st.text_input("氏名")
            reg_phone = st.text_input("電話番号")
            reg_submit = st.form_submit_button("アカウント作成")
            
            if reg_submit:
                try:
                    user_data = {
                        "email": reg_email,
                        "password": reg_password,
                        "full_name": reg_name,
                        "phone_number": reg_phone,
                        "is_admin": True
                    }
                    response = requests.post(f"{API_URL}/register", json=user_data)
                    if response.status_code == 200:
                        st.success("管理者アカウントが作成されました")
                    else:
                        st.error(f"アカウント作成に失敗しました: {response.json()}")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

else:
    # ログアウトボタン
    if st.button("ログアウト", key="logout"):
        st.session_state.token = None
        st.session_state.is_logged_in = False
        st.session_state.user_data = None
        st.rerun()
    
    # タブで機能を切り替え
    tab1, tab2, tab3 = st.tabs(["予約枠管理", "予約一覧", "QRコード読取"])
    
    # 予約枠管理タブ
    with tab1:
        st.header("予約枠管理")
        
        # 予約枠一括作成
        with st.expander("予約枠の一括作成", expanded=True):
            with st.form("create_slots_form"):
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("開始日", value=datetime.now().date())
                with col2:
                    end_date = st.date_input("終了日", value=(datetime.now() + timedelta(days=30)).date())
                
                days = st.multiselect(
                    "曜日選択",
                    options=[
                        {"label": "月曜日", "value": 0},
                        {"label": "火曜日", "value": 1},
                        {"label": "水曜日", "value": 2},
                        {"label": "木曜日", "value": 3},
                        {"label": "金曜日", "value": 4},
                        {"label": "土曜日", "value": 5},
                        {"label": "日曜日", "value": 6}
                    ],
                    format_func=lambda x: x["label"],
                    default=[
                        {"label": "月曜日", "value": 0},
                        {"label": "火曜日", "value": 1},
                        {"label": "水曜日", "value": 2},
                        {"label": "木曜日", "value": 3},
                        {"label": "金曜日", "value": 4}
                    ]
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    start_hour = st.slider("開始時間", 8, 20, 17)
                with col2:
                    end_hour = st.slider("終了時間", 8, 21, 19)
                
                slot_duration = st.selectbox("予約枠の時間", [15, 30, 45, 60], index=1)
                capacity = st.number_input("予約枠の人数", min_value=1, max_value=10, value=2)
                
                submit_slots = st.form_submit_button("予約枠を作成")
                
                if submit_slots:
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state.token}"}
                        days_values = [day["value"] for day in days]
                        
                        data = {
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "end_date": end_date.strftime("%Y-%m-%d"),
                            "days_of_week": days_values,
                            "start_hour": start_hour,
                            "end_hour": end_hour,
                            "slot_duration_minutes": slot_duration,
                            "capacity": capacity
                        }
                        
                        response = requests.post(
                            f"{API_URL}/slots/bulk",
                            headers=headers,
                            json=data
                        )
                        
                        if response.status_code == 200:
                            created_slots = response.json()
                            st.success(f"{len(created_slots)}個の予約枠を作成しました")
                        else:
                            st.error(f"予約枠の作成に失敗しました: {response.json()}")
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")
        
        # 予約枠一覧表示
        st.subheader("予約枠一覧")
        col1, col2 = st.columns(2)
        with col1:
            view_start_date = st.date_input("表示開始日", value=datetime.now().date(), key="view_start")
        with col2:
            view_end_date = st.date_input("表示終了日", value=(datetime.now() + timedelta(days=14)).date(), key="view_end")
        
        if st.button("予約枠を表示", key="show_slots"):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(
                    f"{API_URL}/slots/",
                    headers=headers,
                    params={
                        "start_date": view_start_date.strftime("%Y-%m-%d"),
                        "end_date": view_end_date.strftime("%Y-%m-%d")
                    }
                )
                
                if response.status_code == 200:
                    slots = response.json()
                    if slots:
                        # データフレームに変換
                        slots_data = []
                        for slot in slots:
                            slot_date = datetime.fromisoformat(slot["date"]).strftime("%Y-%m-%d")
                            start_time = datetime.strptime(slot["start_time"], "%H:%M:%S").strftime("%H:%M")
                            end_time = datetime.strptime(slot["end_time"], "%H:%M:%S").strftime("%H:%M")
                            
                            slots_data.append({
                                "ID": slot["id"],
                                "日付": slot_date,
                                "開始時間": start_time,
                                "終了時間": end_time,
                                "定員": slot["capacity"],
                                "残り枠": slot["available_spots"],
                                "予約数": slot["capacity"] - slot["available_spots"]
                            })
                        
                        df = pd.DataFrame(slots_data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("表示する予約枠がありません")
                else:
                    st.error(f"予約枠の取得に失敗しました: {response.json()}")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
    
    # 予約一覧タブ
    with tab2:
        st.header("予約一覧")
        
        # 日付選択
        selected_date = st.date_input("表示する日付", value=datetime.now().date())
        
        if st.button("予約を表示", key="show_reservations"):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(
                    f"{API_URL}/reservations/admin",
                    headers=headers,
                    params={"date": selected_date.strftime("%Y-%m-%d")}
                )
                
                if response.status_code == 200:
                    reservations = response.json()
                    if reservations:
                        # データフレームに変換
                        reservations_data = []
                        for res in reservations:
                            slot_date = datetime.fromisoformat(res["time_slot"]["date"]).strftime("%Y-%m-%d")
                            start_time = datetime.strptime(res["time_slot"]["start_time"], "%H:%M:%S").strftime("%H:%M")
                            
                            reservations_data.append({
                                "予約ID": res["id"],
                                "予約番号": res["daily_number"],
                                "患者名": res["patient"]["full_name"],
                                "電話番号": res["patient"]["phone_number"],
                                "日付": slot_date,
                                "時間": start_time,
                                "確認済み": "✓" if res["is_confirmed"] else "✗",
                                "QRコード": res["qr_code_data"]
                            })
                        
                        df = pd.DataFrame(reservations_data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info(f"{selected_date.strftime('%Y-%m-%d')}の予約はありません")
                else:
                    st.error(f"予約の取得に失敗しました: {response.json()}")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
    
    # QRコード読取タブ
    with tab3:
        st.header("QRコード読取")
        
        # QRコードを手動入力するフォーム
        with st.form("qr_manual_form"):
            qr_code = st.text_input("QRコードの値を入力")
            submit_qr = st.form_submit_button("予約を確認")
            
            if submit_qr and qr_code:
                try:
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    # 予約情報を取得
                    verify_response = requests.get(
                        f"{API_URL}/reservations/{qr_code}",
                        headers=headers
                    )
                    
                    if verify_response.status_code == 200:
                        reservation = verify_response.json()
                        
                        # 予約情報を表示
                        slot_date = datetime.fromisoformat(reservation["time_slot"]["date"]).strftime("%Y-%m-%d")
                        start_time = datetime.strptime(reservation["time_slot"]["start_time"], "%H:%M:%S").strftime("%H:%M")
                        
                        st.success("予約が確認できました")
                        st.write(f"**患者名**: {reservation['patient']['full_name']}")
                        st.write(f"**予約番号**: {reservation['daily_number']}")
                        st.write(f"**日時**: {slot_date} {start_time}")
                        
                        # 確認ステータス
                        if reservation["is_confirmed"]:
                            st.info("この予約は既に確認済みです")
                        else:
                            if st.button("予約を確認済みにする"):
                                confirm_response = requests.put(
                                    f"{API_URL}/reservations/{qr_code}/confirm",
                                    headers=headers
                                )
                                
                                if confirm_response.status_code == 200:
                                    st.success("予約を確認済みにしました")
                                else:
                                    st.error("予約の確認処理に失敗しました")
                    else:
                        st.error("予約が見つかりません")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
        
        # QRコードリーダー（要追加パッケージ）
        st.subheader("QRコードスキャナー")
        st.write("カメラを使用してQRコードをスキャンします")
        
        try:
            from streamlit_qrcode_scanner import qrcode_scanner
            
            qr_code_data = qrcode_scanner()
            if qr_code_data:
                st.write(f"QRコード: {qr_code_data}")
                try:
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    verify_response = requests.get(
                        f"{API_URL}/reservations/{qr_code_data}",
                        headers=headers
                    )
                    
                    if verify_response.status_code == 200:
                        reservation = verify_response.json()
                        
                        # 予約情報を表示（同上）
                        slot_date = datetime.fromisoformat(reservation["time_slot"]["date"]).strftime("%Y-%m-%d")
                        start_time = datetime.strptime(reservation["time_slot"]["start_time"], "%H:%M:%S").strftime("%H:%M")
                        
                        st.success("予約が確認できました")
                        st.write(f"**患者名**: {reservation['patient']['full_name']}")
                        st.write(f"**予約番号**: {reservation['daily_number']}")
                        st.write(f"**日時**: {slot_date} {start_time}")
                        
                        # 確認ステータス
                        if reservation["is_confirmed"]:
                            st.info("この予約は既に確認済みです")
                        else:
                            if st.button("予約を確認済みにする", key="confirm_scanned"):
                                confirm_response = requests.put(
                                    f"{API_URL}/reservations/{qr_code_data}/confirm",
                                    headers=headers
                                )
                                
                                if confirm_response.status_code == 200:
                                    st.success("予約を確認済みにしました")
                                else:
                                    st.error("予約の確認処理に失敗しました")
                    else:
                        st.error("予約が見つかりません")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
        except ImportError:
            st.warning("QRコードスキャナー機能を使用するには、以下のコマンドを実行してください：")
            st.code("pip install streamlit-qrcode-scanner")