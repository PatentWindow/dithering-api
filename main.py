from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from starlette.staticfiles import StaticFiles  # ★ 1. 静的ファイル（ダウンロード）のために追加
import io
import os      # ★ 2. サーバーのURLやファイルパスのために追加
import uuid    # ★ 3. ランダムなファイル名のために追加
from PIL import Image, ImageEnhance

app = FastAPI()

# ★ 4. 一時ファイルを保存するディレクトリを定義
# Render.com の無料枠で書き込み可能な一時ディレクトリ
TEMP_DIR = "/tmp/dithered_files"

# ★ 5. /static パスを作成し、TEMP_DIR を公開
# これにより https://.../static/filename.tiff でアクセス可能になる
app.mount("/static", StaticFiles(directory=TEMP_DIR), name="static")

@app.post("/process-dithering/")
async def process_dithering(
    file: UploadFile = File(...),
    contrast_factor: float = Form(1.0)
):
    try:
        # ★ 6. Render.comが自動で設定する「サーバーの住所」を取得
        base_url = os.environ.get("RENDER_EXTERNAL_URL")
        if not base_url:
            # もし環境変数が見つからなければ、エラーを返す
            print("エラー: 環境変数 RENDER_EXTERNAL_URL が設定されていません。")
            raise HTTPException(status_code=500, detail="サーバー設定エラー: RENDER_EXTERNAL_URL が見つかりません。")

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
        
        # ★ 7. TIFFをファイルとして一時保存
        
        # ディレクトリが存在するか確認し、なければ作成
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # ランダムなファイル名を生成
        unique_filename = f"{uuid.uuid4()}.tiff"
        file_path = os.path.join(TEMP_DIR, unique_filename)
        
        # ファイルをディスクに保存
        img_dithered.save(file_path, format="tiff")
        print(f"TIFFファイルを一時保存しました: {file_path}")

        # ★ 8. Base64の代わりに、ダウンロードURLを生成
        download_url = f"{base_url}/static/{unique_filename}"
        
        # ★ 9. JSONでダウンロードURLを返す
        return JSONResponse(
            status_code=200,
            content={
                "message": "処理に成功しました。ダウンロードURLを返します。",
                "filename": f"dithered_{file.filename}.tiff",
                "download_url": download_url,
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
    return {"message": "画像ディザリングAPI (ダウンロードURL対応版) へようこそ！ /docs にアクセスしてUIを試してください。"}