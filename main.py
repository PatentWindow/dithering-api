from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse  # ★ 修正点 1: Response を JSONResponse に変更
import io
import base64  # ★ 修正点 2: base64をインポート
from PIL import Image, ImageEnhance

app = FastAPI()

@app.post("/process-dithering/")
async def process_dithering(
    file: UploadFile = File(...),
    contrast_factor: float = Form(1.0)
):
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="アップロードされたファイルが画像ではありません。")
        
        contents = await file.read()
        img_color = Image.open(io.BytesIO(contents))
        
        print(f"処理開始: {file.filename}, コントラスト: {contrast_factor}")

        img_grayscale = img_color.convert('L')

        if contrast_factor != 1.0:
            print(f"コントラストを {contrast_factor} に調整します。")
            enhancer = ImageEnhance.Contrast(img_grayscale)
            img_adjusted = enhancer.enhance(contrast_factor)
            img_grayscale = img_adjusted
        else:
            print("コントラストは変更しません (1.0)。")

        print("ディザリング処理が完了しました。")
        img_dithered = img_grayscale.convert(
            '1', 
            dither=Image.Dither.FLOYDSTEINBERG
        )

        tiff_buffer = io.BytesIO()
        img_dithered.save(tiff_buffer, format="tiff")
        tiff_bytes = tiff_buffer.getvalue()
        
        print("TIFF形式でメモリに保存し、Base64にエンコードします。")
        
        # ★ 修正点 3: TIFFデータをBase64のテキスト文字列に変換
        file_base64 = base64.b64encode(tiff_bytes).decode('utf-8')
        output_filename = "dithered_output.tiff" # （このファイル名はJSON内で使われるだけです）

        # ★ 修正点 4: 生のファイルではなく、JSONを返す
        return JSONResponse(
            status_code=200,
            content={
                "message": "処理に成功しました。",
                "filename": output_filename,
                "file_base64": file_base64,
                "mime_type": "image/tiff"
            }
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"画像処理中に予期せぬエラー: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"画像処理中に予期せぬエラーが発生しました: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "画像ディザリングAPI (Base64 JSON対応版) へようこそ！ /docs にアクセスしてUIを試してください。"}