from __future__ import annotations

import asyncio
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from nutrimaster.auth.service import get_current_user
from nutrimaster.web.deps import WebServices, get_services

router = APIRouter()


class FileStorageAdapter:
    def __init__(self, upload_file: UploadFile):
        self._file = upload_file

    def save(self, path):
        with open(path, "wb") as output:
            shutil.copyfileobj(self._file.file, output)


@router.post("/api/personal/upload")
@router.post("/api/library/upload")
async def personal_upload(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    services: WebServices = Depends(get_services),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")
    try:
        library = services.get_personal_lib(user.id)
        info = await asyncio.to_thread(library.upload_pdf, FileStorageAdapter(file), file.filename)
        return JSONResponse({"status": "ok", "file": info})
    except (ValueError, ImportError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/personal/files")
@router.get("/api/library/files")
async def personal_files(
    user=Depends(get_current_user),
    services: WebServices = Depends(get_services),
):
    files = await asyncio.to_thread(services.get_personal_lib(user.id).list_files)
    return JSONResponse({"files": files})


@router.delete("/api/personal/files/{filename}")
@router.delete("/api/library/files/{filename}")
async def personal_delete(
    filename: str,
    user=Depends(get_current_user),
    services: WebServices = Depends(get_services),
):
    ok = await asyncio.to_thread(services.get_personal_lib(user.id).delete_file, filename)
    if ok:
        return JSONResponse({"status": "ok"})
    raise HTTPException(status_code=404, detail="文件不存在")


@router.put("/api/personal/files/{filename}/rename")
@router.put("/api/library/files/{filename}/rename")
async def personal_rename(
    filename: str,
    request: Request,
    user=Depends(get_current_user),
    services: WebServices = Depends(get_services),
):
    data = await request.json()
    new_name = (data.get("new_name") or "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="新文件名不能为空")
    ok = await asyncio.to_thread(services.get_personal_lib(user.id).rename_file, filename, new_name)
    if ok:
        return JSONResponse({"status": "ok"})
    raise HTTPException(status_code=404, detail="文件不存在")
