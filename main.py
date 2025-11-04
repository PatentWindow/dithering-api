from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response  # ★★★ 修正点 1: この行を追加 ★★★
import io
from PIL import Image, ImageEnhance

app = FastAPI()

@app.post("/process-dithering/")
async def process_dithering(
    file: UploadFile = File(...),
    contrast_factor: float = Form(1.0)
):
    try:
        # ファイルが画像かどうかの簡易チェック
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="アップロードされたファイルが画像ではありません。")
        
        # 1. 画像の読み込み
        contents = await file.read()
        img_color = Image.open(io.BytesIO(contents))
        
        # ターミナルに処理開始のログを表示
        print(f"処理開始: {file.filename}, コントラスト: {contrast_factor}")

        # 2. グレースケールに変換
        img_grayscale = img_color.convert('L')

        # 3. コントラスト調整
        if contrast_factor != 1.0:
            print(f"コントラストを {contrast_factor} に調整します。")
            enhancer = ImageEnhance.Contrast(img_grayscale)
            img_adjusted = enhancer.enhance(contrast_factor)
            img_grayscale = img_adjusted
        else:
            print("コントラストは変更しません (1.0)。")


        # 4. Floyd-Steinbergディザリングを適用して1-bit二値画像に変換
        print("ディザリング処理が完了しました。")
        img_dithered = img_grayscale.convert(
            '1', 
            dither=Image.Dither.FLOYDSTEINBERG
        )

        # 5. 結果をTIFF形式でメモリに保存
        tiff_buffer = io.BytesIO()
        img_dithered.save(tiff_buffer, format="tiff")
        tiff_bytes = tiff_buffer.getvalue()
        
        print("TIFF形式でメモリに保存しました。レスポンスを返します。")
        
        # ★★★ 修正点 2: ファイル名を固定 ★★★
        output_filename = "dithered_output.tiff"
        
        # 正常なレスポンスを返す
        return Response(
            content=tiff_bytes,
            media_type="image/tiff",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{output_filename}"
            }
        )

    except HTTPException as e:
        # FastAPIのHTTPExceptionはそのまま再スロー
        raise e
    except Exception as e:
        # その他の予期せぬエラー
        print(f"画像処理中に予期せぬエラー: {e}")
        # エラーの詳細をターミナルに表示
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"画像処理中に予期せぬエラーが発生しました: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "画像ディザリングAPIへようこそ！ /docs にアクセスしてUIを試してください。"}