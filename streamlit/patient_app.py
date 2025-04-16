import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import qrcode
from PIL import Image
import io

# APIのベースURL
API_URL = "http://localhost:8000"

st.set_page_config(page_title="クリニック予約システム", layout="wide")
st.title("クリニック予約システム")

# セッション状態の初期化
if 'token' not in st.session_state:
    st.session_state.token = None
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# QRコード生成関数
def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # PILイメージをバイトストリームに変換
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr

# ログイン状態に応じて表示を切り替え
if not st.session_state.is_logged_in:
    tabs = st.tabs(["ログイン", "新規登録"])
    
    # ログインタブ
    with tabs[0]:
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
                            st.session_state.user_data = user_response.json()
                            st.session_state.is_logged_in = True
                            st.rerun()
                        else:
                            st.error("ユーザー情報の取得に失敗しました")
                    else:
                        st.error("ログインに失敗しました。メールアドレスまたはパスワードが間違っています。")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
    
    # 新規登録タブ
    with tabs[1]:
        st.header("新規登録")
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
                        "phone_number": reg_phone
                    }
                    response = requests.post(f"{API_URL}/register", json=user_data)
                    if response.status_code == 200:
                        st.success("アカウントが作成されました。ログインしてください。")
                    else:
                        st.error(f"アカウント作成に失敗しました: {response.json()}")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
else:
    # ログアウトボタン
    st.write(f"ようこそ、{st.session_state.user_data['full_name']}さん")
    if st.button("ログアウト", key="logout"):
        st.session_state.token = None
        st.session_state.is_logged_in = False
        st.session_state.user_data = None
        st.rerun()
    
    # タブで機能を切り替え
    tab1, tab2 = st.tabs(["予約作成", "予約確認"])
    
    # 予約作成タブ
    with tab1:
        st.header("予約作成")
        
        # 日付選択
        today = datetime.now().date()
        selected_date = st.date_input("日付を選択", value=today, min_value=today)
        
        # 選択した日付の予約枠を取得
        if st.button("利用可能な予約枠を表示", key="show_slots"):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(
                    f"{API_URL}/slots/",
                    headers=headers,
                    params={
                        "start_date": selected_date.strftime("%Y-%m-%d"),
                        "end_date": selected_date.strftime("%Y-%m-%d"),
                        "available_only": True
                    }
                )
                
                if response.status_code == 200:
                    slots = response.json()
                    if slots:
                        st.success(f"{len(slots)}個の予約枠が見つかりました")
                        
                        # 選択肢を作成
                        slot_options = []
                        for slot in slots:
                            start_time = datetime.strptime(slot["start_time"], "%H:%M:%S").strftime("%H:%M")
                            end_time = datetime.strptime(slot["end_time"], "%H:%M:%S").strftime("%H:%M")
                            slot_options.append({
                                "id": slot["id"],
                                "label": f"{start_time} - {end_time} (残り{slot['available_spots']}枠)"
                            })
                        
                        # セッションに保存
                        st.session_state.available_slots = slot_options
                        
                        # 選択フォーム
                        if slot_options:
                            with st.form("reservation_form"):
                                selected_slot = st.selectbox(
                                    "予約枠を選択",
                                    options=slot_options,
                                    format_func=lambda x: x["label"]
                                )
                                
                                submit_reservation = st.form_submit_button("予約する")
                                
                                if submit_reservation:
                                    try:
                                        reservation_data = {
                                            "slot_id": selected_slot["id"]
                                        }
                                        
                                        response = requests.post(
                                            f"{API_URL}/reservations/",
                                            headers=headers,
                                            json=reservation_data
                                        )
                                        
                                        if response.status_code == 200:
                                            reservation = response.json()
                                            st.success("予約が完了しました！")
                                            
                                            # QRコードを表示
                                            qr_data = reservation["qr_code_data"]
                                            qr_img = generate_qr_code(qr_data)
                                            
                                            st.write(f"予約番号: {reservation['daily_number']}")
                                            st.image(qr_img, caption="予約確認用QRコード", width=300)
                                            st.info("このQRコードは予約確認時に必要です。スクリーンショットを撮るか、「予約確認」タブで確認できます。")
                                        else:
                                            error_msg = response.json().get("detail", "予約に失敗しました")
                                            st.error(f"予約に失敗しました: {error_msg}")
                                    except Exception as e:
                                        st.error(f"エラーが発生しました: {e}")
                    else:
                        st.info(f"{selected_date.strftime('%Y-%m-%d')}の予約枠はありません")
                else:
                    st.error(f"予約枠の取得に失敗しました: {response.json()}")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
    
    # 予約確認タブ
    with tab2:
        st.header("予約確認")
        
        # 予約一覧を取得
        if st.button("予約を表示", key="show_reservations"):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(
                    f"{API_URL}/reservations/",
                    headers=headers,
                    params={"include_past": True}
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
                                "日付": slot_date,
                                "時間": start_time,
                                "確認済み": "はい" if res["is_confirmed"] else "いいえ",
                                "QRデータ": res["qr_code_data"]
                            })
                        
                        st.session_state.reservations = reservations
                        df = pd.DataFrame(reservations_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # 詳細表示セクション
                        st.subheader("予約詳細とQRコード")
                        
                        # 予約選択
                        reservation_ids = [res["id"] for res in reservations]
                        reservation_labels = [f"予約番号 {res['daily_number']} - {datetime.fromisoformat(res['time_slot']['date']).strftime('%Y-%m-%d')} {datetime.strptime(res['time_slot']['start_time'], '%H:%M:%S').strftime('%H:%M')}" for res in reservations]
                        
                        selected_index = st.selectbox(
                            "予約を選択",
                            options=range(len(reservation_ids)),
                            format_func=lambda i: reservation_labels[i]
                        )
                        
                        # 選択した予約の詳細表示
                        selected_reservation = reservations[selected_index]
                        slot_date = datetime.fromisoformat(selected_reservation["time_slot"]["date"]).strftime("%Y-%m-%d")
                        start_time = datetime.strptime(selected_reservation["time_slot"]["start_time"], "%H:%M:%S").strftime("%H:%M")
                        
                        st.write(f"**予約番号**: {selected_reservation['daily_number']}")
                        st.write(f"**日時**: {slot_date} {start_time}")
                        st.write(f"**状態**: {'確認済み' if selected_reservation['is_confirmed'] else '未確認'}")
                        
                        # QRコード表示
                        qr_data = selected_reservation["qr_code_data"]
                        qr_img = generate_qr_code(qr_data)
                        st.image(qr_img, caption="予約確認用QRコード", width=300)
                        
                        # キャンセルボタン
                        if not selected_reservation["is_confirmed"]:
                            if st.button("予約をキャンセル", key=f"cancel_{selected_reservation['id']}"):
                                cancel_response = requests.delete(
                                    f"{API_URL}/reservations/{selected_reservation['id']}",
                                    headers=headers
                                )
                                
                                if cancel_response.status_code == 204:
                                    st.success("予約をキャンセルしました")
                                    st.rerun()
                                else:
                                    st.error("予約のキャンセルに失敗しました")
                        else:
                            st.warning("確認済みの予約はキャンセルできません")
                    else:
                        st.info("予約がありません")
                else:
                    st.error(f"予約の取得に失敗しました: {response.json()}")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")