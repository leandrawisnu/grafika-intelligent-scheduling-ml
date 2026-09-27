import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import EkstrakJadwalResponse
from app.services.jadwal_ekstrak import excel_ke_teks, pdf_ke_muatan, susun_baris

router = APIRouter()

BATAS_BERKAS = 15 * 1024 * 1024


@router.post("/jadwal/ekstrak", response_model=EkstrakJadwalResponse)
async def ekstrak_jadwal(
    berkas: UploadFile = File(...),
    katalog: str = Form("{}"),
):
    mentah = await berkas.read()
    if not mentah:
        raise HTTPException(status_code=400, detail="Berkas kosong")
    if len(mentah) > BATAS_BERKAS:
        raise HTTPException(status_code=413, detail="Berkas melebihi 15 MB")
    try:
        katalog_obj = json.loads(katalog) if katalog else {}
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=400, detail="Katalog tidak valid") from err
    if not isinstance(katalog_obj, dict):
        raise HTTPException(status_code=400, detail="Katalog tidak valid")

    nama = (berkas.filename or "").lower()
    try:
        if nama.endswith(".xlsx"):
            baris = susun_baris(excel_ke_teks(mentah), katalog_obj, None)
        elif nama.endswith(".pdf"):
            teks, gambar = pdf_ke_muatan(mentah)
            baris = susun_baris(teks, katalog_obj, gambar)
        else:
            raise HTTPException(status_code=400, detail="Hanya PDF atau Excel .xlsx")
    except HTTPException:
        raise
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    except Exception as err:
        pesan = str(err)
        if "sk-" in pesan:
            pesan = "panggilan model gagal"
        raise HTTPException(status_code=502, detail=f"Ekstraksi gagal: {pesan[:300]}") from err
    return EkstrakJadwalResponse(baris=baris)
