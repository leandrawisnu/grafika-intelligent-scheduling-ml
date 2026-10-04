"""Endpoint AI import dokumen: parsing universal + pemetaan ke master GIS."""
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import ImportPlan, IngestMapRequest, IngestParseResponse
from app.services.ingest_common import IngestConfigError, IngestServiceError, pesan_aman
from app.services.ingest_mapper import petakan_dokumen
from app.services.llamaparse_client import parse_dokumen

router = APIRouter()
log = logging.getLogger("gis.ingest")

BATAS_BERKAS = 15 * 1024 * 1024


@router.post("/ingest/parse", response_model=IngestParseResponse)
async def ingest_parse(berkas: UploadFile = File(...)):
    mentah = await berkas.read()
    if not mentah:
        raise HTTPException(status_code=400, detail="Berkas kosong")
    if len(mentah) > BATAS_BERKAS:
        raise HTTPException(status_code=413, detail="Berkas melebihi 15 MB")

    try:
        hasil = parse_dokumen(berkas.filename or "dokumen", mentah)
    except IngestConfigError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except IngestServiceError as err:
        raise HTTPException(status_code=502, detail=f"Parsing gagal: {err}") from err
    except Exception as err:  # noqa: BLE001
        log.exception("ingest parse gagal")
        raise HTTPException(status_code=502, detail=f"Parsing gagal: {pesan_aman(err)}") from err
    return IngestParseResponse(**hasil)


@router.post("/ingest/petakan", response_model=ImportPlan)
def ingest_petakan(req: IngestMapRequest):
    try:
        return petakan_dokumen(req.teks, req.konteks)
    except IngestConfigError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    except IngestServiceError as err:
        raise HTTPException(status_code=502, detail=str(err)) from err
    except Exception as err:  # noqa: BLE001
        log.exception("ingest petakan gagal")
        raise HTTPException(status_code=502, detail=f"Pemetaan gagal: {pesan_aman(err)}") from err
