import json
import os
import logging
import warnings
from dotenv import load_dotenv
from google import genai
from PIL import Image

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.ERROR)
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)

load_dotenv()

def analyze_receipt(image_path: str) -> dict:
    """
    レシート画像をGemini APIに送信し、構造化されたデータ（辞書型）として返す関数
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("エラー: GEMINI_API_KEYが.envファイルに見つかりません。")
        return None
    
    client = genai.Client(api_key=api_key)

    image = Image.open(image_path)

    prompt = """
    添付されたレシート画像を貝瀬益し、以下の情報を指定されたJSON形式のみで出力してください。
    余計な解説文や Markdown表記(```json ... ```)は一切含めず、純粋なJSON文字のみを返してください。
    
    【抽出項目】
    - date: 購入日（形式: YYYY-MM-DD）。不明な場合は本日の日付や推定。
    - store: 店舗名（例: 〇〇スーパー、コンビニ名など）
    - amount: 合計金額（数値のみ、カンマなしの整数）
    - category: カテゴリ（「食費」「日用品」「交通費」「交際費」「その他」の中から1つ選ぶ）

    【出力フォーマット例】
    {
        "date": "2023-09-15",
        "store": "サンプルスーパー",
        "amount": 1500,
        "category": "食費"
    }
    """

    try:
        response = client.models.generate_content(
            model= "gemini-3.6-flash",
            contents=[image, prompt]
        )

        result_text = response.text.strip()

        if result_text.startswith("```"):
            lines = result_text.splitlines()
            result_text = "\n".join(lines[1:-1])

        data = json.loads(result_text)
        return data

    except json.JSONDecodeError:
        print("エラー：AIからの返答をJSONとしてパースできませんでした。")
        print(f"返答内容：{response.text}")
        return None
    except Exception as e:
        print(f"OCR処理エラー：{e}")
        return None

if __name__ == "__main__":
    test_image_path = "test_receipt.jpg"
    print(f"{test_image_path} を解析中...")
    result = analyze_receipt(test_image_path)
    if result:
        print("\n--- 解析結果 ---")
        print(f"日付：{result.get('date')}")
        print(f"店舗：{result.get('store')}")
        print(f"金額：{result.get('amount')}円")
        print(f"カテゴリ：{result.get('category')}")