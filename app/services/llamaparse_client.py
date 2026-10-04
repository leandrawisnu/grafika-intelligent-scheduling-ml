"""Klien LlamaParse (REST v2) untuk parsing dokumen format apa pun.

Alur: unggah berkas -> buat job parse -> poll sampai COMPLETED -> ambil markdown/teks.
Dipakai mode sinkron di dalam request ML (SDK Go memanggil endpoint /ingest/parse).
"""
import time

import httpx

from app.config import (
    LLAMA_CLOUD_API_KEY,
    LLAMA_OCR_LANGUAGES,
    LLAMA_PARSE_TIER,
    LLAMA_PARSE_TIMEOUT_SECONDS,
)
from app.services.ingest_common import IngestConfigError, IngestServiceError, pesan_aman

BASE_URL = "https://api.cloud.llamaindex.ai"
PATH_UNGGAH = "/api/v1/beta/files"
PATH_PARSE = "/api/v2/parse"

TIER_VALID = {"fast", "cost_effective", "agentic", "agentic_plus"}
TIER_DEFAULT = "agentic"
JEDA_POLL_DETIK = 2.0
STATUS_AKHIR = {"COMPLETED", "FAILED", "CANCELLED", "ERROR"}


def _bahasa_ocr() -> list[str]:
    return [bagian.strip() for bagian in LLAMA_OCR_LANGUAGES.split(",") if bagian.strip()]


def parse_dokumen(nama: str, isi: bytes) -> dict:
    """Parse dokumen apa pun, kembalikan {markdown, teks, jumlah_halaman, peringatan}."""
    if not LLAMA_CLOUD_API_KEY:
        raise IngestConfigError("LLAMA_CLOUD_API_KEY belum diisi")

    tier = LLAMA_PARSE_TIER if LLAMA_PARSE_TIER in TIER_VALID else TIER_DEFAULT
    peringatan: list[str] = []
    batas = time.monotonic() + LLAMA_PARSE_TIMEOUT_SECONDS
    klien = httpx.Client(timeout=httpx.Timeout(120.0, connect=20.0))
    try:
        berkas_id = _unggah(klien, nama, isi)
        job_id = _buat_job(klien, berkas_id, tier, peringatan)
        data = _tunggu_hasil(klien, job_id, batas)
    except httpx.HTTPStatusError as err:
        raise IngestServiceError(
            f"LlamaParse HTTP {err.response.status_code}: {pesan_aman(err, 200)}"
        ) from err
    except httpx.HTTPError as err:
        raise IngestServiceError(f"LlamaParse tidak dapat dihubungi: {pesan_aman(err)}") from err
    finally:
        klien.close()

    markdown = _halaman_jadi_teks(data.get("markdown"), "markdown")
    teks = _halaman_jadi_teks(data.get("text"), "text")
    if not markdown and teks:
        markdown = teks
    if not markdown:
        raise IngestServiceError("LlamaParse tidak mengembalikan teks (dokumen mungkin kosong).")
    jumlah_halaman = _jumlah_halaman(data)
    return {
        "markdown": markdown,
        "teks": teks,
        "jumlah_halaman": jumlah_halaman,
        "peringatan": peringatan,
    }


def _unggah(klien: httpx.Client, nama: str, isi: bytes) -> str:
    resp = klien.post(
        BASE_URL + PATH_UNGGAH,
        headers={"Authorization": f"Bearer {LLAMA_CLOUD_API_KEY}"},
        data={"purpose": "parse"},
        files={"file": (nama or "dokumen", isi)},
    )
    resp.raise_for_status()
    berkas_id = resp.json().get("id")
    if not berkas_id:
        raise IngestServiceError("LlamaParse tidak mengembalikan id berkas.")
    return berkas_id


def _buat_job(klien: httpx.Client, berkas_id: str, tier: str, peringatan: list[str]) -> str:
    dasar = {"file_id": berkas_id, "tier": tier, "version": "latest"}
    bahasa = _bahasa_ocr()
    upaya = []
    if bahasa:
        upaya.append(
            {
                **dasar,
                "input_options": {"image": {"camera_photo_correction": True}},
                "processing_options": {"ocr_parameters": {"languages": bahasa}},
            }
        )
    upaya.append(dasar)

    for i, body in enumerate(upaya):
        resp = klien.post(
            BASE_URL + PATH_PARSE,
            headers={"Authorization": f"Bearer {LLAMA_CLOUD_API_KEY}"},
            json=body,
        )
        if resp.status_code == 400 and i < len(upaya) - 1:
            peringatan.append("Pengaturan OCR bahasa ditolak LlamaParse, memakai pengaturan default.")
            continue
        resp.raise_for_status()
        job_id = resp.json().get("id")
        if not job_id:
            raise IngestServiceError("LlamaParse tidak mengembalikan id job.")
        return job_id
    raise IngestServiceError("LlamaParse menolak permintaan parse.")


def _tunggu_hasil(klien: httpx.Client, job_id: str, batas: float) -> dict:
    while True:
        resp = klien.get(
            f"{BASE_URL}{PATH_PARSE}/{job_id}",
            headers={"Authorization": f"Bearer {LLAMA_CLOUD_API_KEY}"},
            params={"expand": "markdown,text"},
            timeout=httpx.Timeout(60.0, connect=15.0),
        )
        resp.raise_for_status()
        data = resp.json()
        status = str((data.get("job") or {}).get("status") or data.get("status") or "").upper()
        if status in STATUS_AKHIR:
            if status != "COMPLETED":
                raise IngestServiceError(f"LlamaParse berhenti dengan status {status}.")
            return data
        if time.monotonic() > batas:
            raise IngestServiceError("Waktu proses LlamaParse habis (timeout).")
        time.sleep(JEDA_POLL_DETIK)


def _halaman_jadi_teks(bagian: object, kunci: str) -> str:
    if not isinstance(bagian, dict):
        return ""
    halaman = bagian.get("pages")
    if not isinstance(halaman, list):
        return ""
    potongan: list[str] = []
    for item in halaman:
        if not isinstance(item, dict):
            continue
        isi = item.get(kunci) or item.get("text") or item.get("markdown") or ""
        if isi:
            potongan.append(str(isi).strip())
    return "\n\n".join(potongan).strip()


def _jumlah_halaman(data: dict) -> int:
    jumlah = 0
    for kunci in ("markdown", "text"):
        bagian = data.get(kunci)
        if isinstance(bagian, dict) and isinstance(bagian.get("pages"), list):
            jumlah = max(jumlah, len(bagian["pages"]))
    return jumlah
