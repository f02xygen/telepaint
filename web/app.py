import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from database import get_post_record, update_post_image

web_app = FastAPI()

# Подключаем папку с шаблонами
templates = Jinja2Templates(directory="templates")


@web_app.get("/draw/{post_id}")
async def get_draw_page(request: Request, post_id: str):
    post = await get_post_record(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return templates.TemplateResponse(
        request=request,
        name="draw.html",
        context={
            "post": post,
            "post_id": post_id,
            "id": post_id,
            "is_expired": False
        }
    )


@web_app.get("/media_file/{filename}")
async def get_media_file(filename: str):
    path = os.path.join("media", filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@web_app.post("/api/post/{post_id}/update")
async def update_post_drawing(post_id: str, file: UploadFile = File(...)):
    post = await get_post_record(post_id)
    if not post or post.is_expired:
        raise HTTPException(status_code=400, detail="Forbidden or expired")

    content = await file.read()
    with open(post.current_image_path, "wb") as f:
        f.write(content)

    await update_post_image(post_id)
    return {"status": "ok"}