〇AIレシート家計簿アプリ

Gemini APIの画像OCR機能を活用し、レシート画像から「日付・店舗名・金額・カテゴリ」を自動抽出して記録・管理できるWebアプリケーションである。

・主な機能
ユーザー認証機能：アカウント作成・ログイン・ログアウト機能（パスワードはハッシュ化して完全に保存）。
AIレシートOCR読み取り：レシート画像をアップロードすると、Gemini APIが自動解析して情報を構造抽象化。
データの確認・自己修正：AIの解析結果を確認し、手動で修正・保存が可能。
支出の集計・グラフ化：日・月・年単位での合計支出計算、カテゴリ別の内訳グラフ表示。
データの個別削除：不要になった記録の削除機能。
セキュリティ管理：ログインユーザー本人のデータのみを閲覧・操作できるデータ分離構造。

・使用技術スタック

Language: Python 3.13
Fronted / UI: Streamlit
AI / OCR: Gemini API (`google-genai`)
Database: SQLite3
Environment Management: `python-dotenv`
Deployment: Streamlit Community Cloud

・ローカル環境での起動方法
---bash---
git clone [https://github.com/stonewell627/ai-kakeibo-app.git]
cd ai-kakeibo-app
