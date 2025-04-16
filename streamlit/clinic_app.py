import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# APIのベースURL
API_URL = "http://localhost:8000"

st.set_page_config(page_title="クリニック予約確認システム", layout="wide")
st.title("クリニック予約確認システム")

# セッション状態の初期化
if 'token' not in st.session_state:
    st.session_state.token = None
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

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
                            st.experimental_rerun()
                        else:
                            st.error("管理者権限がありません")
                    else:
                        st.error("ユーザー情報の取得に失敗しました")
                else:
                    st.error("ログインに失敗しました。メールアドレスまたはパスワードが間違っています。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
else:
    # ログアウトボタン
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"ようこそ、{st.session_state.user_data['full_name']}さん")
    with col2:
        if st.button("ログアウト", key="logout"):
            st.session_state.token = None
            st.session_state.is_logged_in = False
            st.session_state.user_data = None
            st.experimental_rerun()
    
    # タブで機能を切り替え
    tab1, tab2 = st.tabs(["QRコード読取", "本日の予約一覧"])
    
    # QRコード読取タブ
    with tab1:
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
                            # 確認ボタン
                            if st.button("予約を確認済みにする"):
                                confirm_response = requests.put(
                                    f"{API_URL}/reservations/{qr_code}/confirm",
                                    headers=headers
                                )
                                
                                if confirm_response.status_code == 200:
                                    st.success("予約を確認済みにしました")
                                    st.balloons()  # お祝い効果
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
                            # 確認ボタン
                            if st.button("予約を確認済みにする", key="confirm_scanned"):
                                confirm_response = requests.put(
                                    f"{API_URL}/reservations/{qr_code_data}/confirm",
                                    headers=headers
                                )
                                
                                if confirm_response.status_code == 200:
                                    st.success("予約を確認済みにしました")
                                    st.balloons()  # お祝い効果
                                else:
                                    st.error("予約の確認処理に失敗しました")
                    else:
                        st.error("予約が見つかりません")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
        except ImportError:
            st.warning("QRコードスキャナー機能を使用するには、以下のコマンドを実行してください：")
            st.code("pip install streamlit-qrcode-scanner")
    
    # 本日の予約一覧タブ
    with tab2:
        st.header("本日の予約一覧")
        
        today = datetime.now().date()
        
        if st.button("予約を表示", key="show_today_reservations"):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(
                    f"{API_URL}/reservations/admin",
                    headers=headers,
                    params={"date": today.strftime("%Y-%m-%d")}
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
                                "予約番号": res["daily_number"],
                                "患者名": res["patient"]["full_name"],
                                "電話番号": res["patient"]["phone_number"],
                                "時間": start_time,
                                "確認済み": "✓" if res["is_confirmed"] else "✗"
                            })
                        
                        df = pd.DataFrame(reservations_data)
                        
                        # 確認済みと未確認でフィルタリング
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("未確認の予約")
                            unconfirmed = df[df["確認済み"] == "✗"]
                            if not unconfirmed.empty:
                                st.dataframe(unconfirmed, use_container_width=True)
                            else:
                                st.info("未確認の予約はありません")
                        
                        with col2:
                            st.subheader("確認済みの予約")
                            confirmed = df[df["確認済み"] == "✓"]
                            if not confirmed.empty:
                                st.dataframe(confirmed, use_container_width=True)
                            else:
                                st.info("確認済みの予約はありません")
                                
                        # 統計情報
                        st.subheader("統計")
                        total = len(reservations)
                        confirmed_count = len(confirmed)
                        unconfirmed_count = len(unconfirmed)
                        
                        st.write(f"本日の予約総数: {total}")
                        st.write(f"確認済み: {confirmed_count} ({confirmed_count/total*100:.1f}%)")
                        st.write(f"未確認: {unconfirmed_count} ({unconfirmed_count/total*100:.1f}%)")
                        
                    else:
                        st.info(f"{today.strftime('%Y-%m-%d')}の予約はありません")
                else:
                    st.error(f"予約の取得に失敗しました: {response.json()}")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")