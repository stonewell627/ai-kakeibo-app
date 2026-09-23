import os
import datetime
import pandas as pd
import streamlit as st
import database
import ocr

database.init_db()

st.set_page_config(page_title="AIレシート家計簿", page_icon="📄", layout="centered")

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("AIレシート家計簿")
    
    auth_mode = st.radio("選択してください", ["ログイン", "新規アカウント作成"], horizontal=True)

    if auth_mode == "ログイン":
        st.subheader("ログイン")
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")
        
        if st.button("ログイン", type="primary"):
            user = database.login_user(username, password)
            if user:
                st.session_state.user = user
                st.success(f"ようこそ、{user['username']} さん！")
                st.rerun()
            else:
                st.error("ユーザー名またはパスワードが正しくありません。")

    elif auth_mode == "新規アカウント作成":
        st.subheader("新規アカウント作成")
        new_username = st.text_input("希望のユーザー名")
        new_password = st.text_input("希望のパスワード", type="password")
        
        if st.button("アカウント作成", type="primary"):
            if new_username and new_password:
                if database.register_user(new_username, new_password):
                    st.success("アカウントが作成されました。「ログイン」に切り替えてログインしてください。")
                else:
                    st.error("そのユーザー名は既に使用されています。別の名前をお試しください。")
            else:
                st.warning("ユーザー名とパスワードの両方を入力してください。")

else:
    user = st.session_state.user

    st.sidebar.write(f"ログイン中: **{user['username']}** さん")
    if st.sidebar.button("ログアウト"):
        st.session_state.user = None
        st.session_state.ocr_result = None
        st.rerun()

    st.title("AIレシート家計簿")

    menu = st.sidebar.radio("メニューを選択してください", ["画像を添付", "家計簿を見る"])

    if menu == "画像を添付":
        st.header("レシート画像の読み取り")
        st.write("レシート写真をアップロードすると、AIが「日付・店舗名・金額・カテゴリ」を自動読み取りします。")
        uploaded_file = st.file_uploader("レシート画像をアップロードしてください", type=["jpg", "jpeg", "png"])

        if "ocr_result" not in st.session_state:
            st.session_state.ocr_result = None

        if uploaded_file is not None:
            st.image(uploaded_file, caption="アップロード画像", use_container_width=True)

            if st.button("レシートを解析する", type="primary"):
                with st.spinner("AIがレシートを解析中…"):
                    temp_path = "temp_uploaded_receipt.jpg"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    result = ocr.analyze_receipt(temp_path)

                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                    if result:
                        st.session_state.ocr_result = result
                        st.success("解析が完了しました。内容を確認・修正してください。")
                    else:
                        st.error("解析に失敗しました。もう一度試すか手動で修正して下さい。")

        if st.session_state.ocr_result:
            st.subheader("読み取り結果の確認・自己修正")
            res = st.session_state.ocr_result

            try:
                default_date = datetime.datetime.strptime(res.get("date", ""), "%Y-%m-%d").date()
            except ValueError:
                default_date = datetime.date.today()

            categories = ["食事", "日用品", "交通費", "交際費", "その他"]
            cat_index = categories.index(res.get("category")) if res.get("category") in categories else 0

            with st.form("expense_form"):
                date_val = st.date_input("購入日", value=default_date)
                store_val = st.text_input("店舗名", value=res.get("store", ""))
                amount_val = st.number_input("合計金額（円）", value=int(res.get("amount", 0)), step=1)
                category_val = st.selectbox("カテゴリ", categories, index=cat_index)

                submit_button = st.form_submit_button("家計簿に記録する")

                if submit_button:
                    str_date = date_val.strftime("%Y-%m-%d")
                    success = database.add_expense(user["id"], str_date, store_val, int(amount_val), category_val)

                    if success:
                        st.success("家計簿に正常に記録されました！")
                        st.session_state.ocr_result = None
                    else:
                        st.error("データベースへの書き込みに失敗しました。")

    elif menu == "家計簿を見る":
        st.header("家計簿を見る")
        st.write("いつのを見ますか？表示したい単位と時期を選択してください。")

        period_type = st.radio("表示単位", ["日", "月", "年"], horizontal=True)

        target_str = ""
        today = datetime.date.today()

        if period_type == "日":
            selected_date = st.date_input("日付を選択してください", value=today)
            target_str = selected_date.strftime("%Y-%m-%d")

        elif period_type == "月":
            col1, col2 = st.columns(2)
            with col1:
                selected_year = st.number_input("年", min_value=2000, max_value=2100, value=today.year)
            with col2:
                selected_month = st.number_input("月", min_value=1, max_value=12, value=today.month)
            target_str = f"{selected_year:04d}-{selected_month:02d}"

        elif period_type == "年":
            selected_year = st.number_input("年を選択してください", min_value=2000, max_value=2100, value=today.year)
            target_str = f"{selected_year:04d}"

        st.divider()

        records = database.get_expenses_by_period(user["id"], period_type, target_str)

        if records:
            df = pd.DataFrame(records)

            total_amount = df["amount"].sum()
            st.metric(label=f" 【{target_str}】の合計支出", value=f"{total_amount:,}円")

            st.subheader("カテゴリ別内訳")
            category_sum = df.groupby("category")["amount"].sum().reset_index()
            st.bar_chart(data=category_sum, x="category", y="amount")

            st.subheader("支出明細とデータの削除")

            display_df = df[["id", "date", "store", "category", "amount"]].rename(
                columns={"id": "ID", "date": "日付", "store": "店舗名", "category": "カテゴリ", "amount": "金額(円)"}
            )
            st.dataframe(display_df, use_container_width=True)

            st.caption("削除したいデータがある場合は、対象のIDを選んで削除ボタンを押してください。")
            delete_target_id = st.selectbox("削除するデータのIDを選択", options=df["id"].tolist())
            
            if st.button("選択したデータを削除する", type="secondary"):
                if database.delete_expense(delete_target_id, user["id"]):
                    st.success(f"ID: {delete_target_id} のデータを削除しました。")
                    st.rerun()
                else:
                    st.error("データの削除に失敗しました。")

        else:
            st.info(f"【{target_str}】の記録データはありません。")