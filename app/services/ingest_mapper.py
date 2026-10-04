"""Pemetaan hasil parsing dokumen ke master GIS via LLM (OpenRouter).

Memakai structured outputs JSON-schema; bila endpoint model tidak mendukung,
otomatis turun ke mode tanpa penegakan parameter, lalu perbaikan 1x bila
jawaban bukan JSON valid.
"""
import json

import httpx
from pydantic import ValidationError

from app.config import (
    INGEST_MAX_OUTPUT_TOKENS,
    INGEST_MAX_TEKS,
    INGEST_MODEL,
    INGEST_TIMEOUT_SECONDS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
)
from app.models.schemas import ImportPlan
from app.prompts import INGEST_MAP_PROMPT
from app.services.ingest_common import IngestConfigError, IngestServiceError, pesan_aman

_NULL_STR = {"type": ["string", "null"]}

PLAN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "jenis_dokumen",
        "ringkasan",
        "keyakinan",
        "peringatan",
        "master_usulan",
        "baris_jadwal",
    ],
    "properties": {
        "jenis_dokumen": {
            "type": "string",
            "enum": ["jadwal", "master", "campuran", "tidak_dikenali"],
        },
        "ringkasan": {"type": "string"},
        "keyakinan": {"type": "number"},
        "peringatan": {"type": "array", "items": {"type": "string"}},
        "master_usulan": {
            "type": "object",
            "additionalProperties": False,
            "required": ["guru", "mata_pelajaran", "ruangan", "kelas", "jurusan"],
            "properties": {
                "guru": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["ref", "nama", "nip", "aksi"],
                        "properties": {
                            "ref": {"type": "string"},
                            "nama": {"type": "string"},
                            "nip": _NULL_STR,
                            "aksi": {"type": "string", "enum": ["buat"]},
                        },
                    },
                },
                "mata_pelajaran": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["ref", "nama", "kode", "jam_wajib_per_minggu", "tingkat", "aksi"],
                        "properties": {
                            "ref": {"type": "string"},
                            "nama": {"type": "string"},
                            "kode": _NULL_STR,
                            "jam_wajib_per_minggu": {"type": ["number", "null"]},
                            "tingkat": {"type": ["integer", "null"]},
                            "aksi": {"type": "string", "enum": ["buat"]},
                        },
                    },
                },
                "ruangan": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["ref", "nama", "kode", "tipe_ruangan", "kapasitas", "aksi"],
                        "properties": {
                            "ref": {"type": "string"},
                            "nama": {"type": "string"},
                            "kode": _NULL_STR,
                            "tipe_ruangan": _NULL_STR,
                            "kapasitas": {"type": ["integer", "null"]},
                            "aksi": {"type": "string", "enum": ["buat"]},
                        },
                    },
                },
                "kelas": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["ref", "nama", "kode", "tingkat", "jurusan_id", "jurusan_ref", "aksi"],
                        "properties": {
                            "ref": {"type": "string"},
                            "nama": {"type": "string"},
                            "kode": _NULL_STR,
                            "tingkat": {"type": ["integer", "null"]},
                            "jurusan_id": _NULL_STR,
                            "jurusan_ref": _NULL_STR,
                            "aksi": {"type": "string", "enum": ["buat"]},
                        },
                    },
                },
                "jurusan": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["ref", "nama", "kode", "aksi"],
                        "properties": {
                            "ref": {"type": "string"},
                            "nama": {"type": "string"},
                            "kode": _NULL_STR,
                            "aksi": {"type": "string", "enum": ["buat"]},
                        },
                    },
                },
            },
        },
        "baris_jadwal": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "hari", "jam", "kelas", "mata_pelajaran", "guru", "ruangan",
                    "hari_id", "jam_pelajaran_id", "kelas_id", "mata_pelajaran_id", "guru_id", "ruangan_id",
                    "kelas_ref", "mapel_ref", "guru_ref", "ruangan_ref",
                    "status", "keyakinan", "catatan",
                ],
                "properties": {
                    "hari": {"type": "string"},
                    "jam": {"type": "string"},
                    "kelas": {"type": "string"},
                    "mata_pelajaran": {"type": "string"},
                    "guru": {"type": "string"},
                    "ruangan": {"type": "string"},
                    "hari_id": _NULL_STR,
                    "jam_pelajaran_id": _NULL_STR,
                    "kelas_id": _NULL_STR,
                    "mata_pelajaran_id": _NULL_STR,
                    "guru_id": _NULL_STR,
                    "ruangan_id": _NULL_STR,
                    "kelas_ref": _NULL_STR,
                    "mapel_ref": _NULL_STR,
                    "guru_ref": _NULL_STR,
                    "ruangan_ref": _NULL_STR,
                    "status": {
                        "type": "string",
                        "enum": ["siap", "akan_dibuat", "perlu_pilihan", "sudah_ada"],
                    },
                    "keyakinan": {"type": "number"},
                    "catatan": {"type": "string"},
                },
            },
        },
    },
}


class _ParameterTidakDidukung(Exception):
    """Endpoint model menolak parameter (mis. structured outputs)."""


def petakan_dokumen(teks: str, konteks: dict) -> ImportPlan:
    if not OPENROUTER_API_KEY:
        raise IngestConfigError("OPENROUTER_API_KEY belum diisi")
    teks = (teks or "").strip()
    if not teks:
        raise IngestServiceError("Teks dokumen kosong, tidak ada yang bisa dipetakan.")
    if len(teks) > INGEST_MAX_TEKS:
        raise IngestServiceError(
            "Dokumen terlalu besar untuk dianalisis sekaligus. Impor per bagian atau per jurusan."
        )

    pesan = _susun_pesan(teks, konteks)
    pesan_terakhir = ""
    for opsi in _opsi_permintaan():
        try:
            konten = _kirim(pesan, opsi)
        except _ParameterTidakDidukung as err:
            pesan_terakhir = str(err)
            continue

        plan = _validasi(konten)
        if plan is not None:
            return plan

        konten_perbaikan = _kirim(_pesan_perbaikan(pesan, konten), {})
        plan = _validasi(konten_perbaikan)
        if plan is not None:
            return plan
        raise IngestServiceError(
            "Model AI tidak mengembalikan JSON sesuai skema. Coba ulangi analisis."
        )

    raise IngestServiceError(
        f"Model AI menolak permintaan pemetaan: {pesan_aman(Exception(pesan_terakhir))}"
    )


def _opsi_permintaan() -> list[dict]:
    response_format = {
        "type": "json_schema",
        "json_schema": {"name": "import_plan", "strict": True, "schema": PLAN_SCHEMA},
    }
    return [
        {"response_format": response_format, "provider": {"require_parameters": True}},
        {"response_format": response_format},
        {},
    ]


def _susun_pesan(teks: str, konteks: dict) -> list[dict]:
    konteks_json = json.dumps(konteks, ensure_ascii=False, separators=(",", ":"))
    isi = INGEST_MAP_PROMPT.replace("{konteks}", konteks_json).replace("{teks}", teks)
    return [{"role": "user", "content": isi}]


def _pesan_perbaikan(pesan: list[dict], konten: str) -> list[dict]:
    return pesan + [
        {"role": "assistant", "content": konten[:20000]},
        {
            "role": "user",
            "content": "Balasan sebelumnya bukan JSON valid sesuai skema. Jawab ULANG hanya dengan satu objek JSON valid sesuai skema, tanpa teks lain.",
        },
    ]


def _kirim(pesan: list[dict], opsi: dict) -> str:
    body = {
        "model": INGEST_MODEL,
        "messages": pesan,
        "temperature": 0.1,
        "max_tokens": INGEST_MAX_OUTPUT_TOKENS,
    }
    body.update(opsi)
    try:
        resp = httpx.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "X-Title": "GIS Ingest",
            },
            json=body,
            timeout=httpx.Timeout(INGEST_TIMEOUT_SECONDS, connect=15.0),
        )
    except httpx.HTTPError as err:
        raise IngestServiceError(f"Model AI tidak dapat dihubungi: {pesan_aman(err)}") from err

    if resp.status_code in (400, 404, 422) and opsi:
        raise _ParameterTidakDidukung(
            f"HTTP {resp.status_code}: {pesan_aman(Exception(resp.text), 200)}"
        )
    if resp.status_code >= 400:
        raise IngestServiceError(
            f"Model AI HTTP {resp.status_code}: {pesan_aman(Exception(resp.text), 200)}"
        )

    try:
        data = resp.json()
    except ValueError as err:
        raise IngestServiceError("Jawaban model AI bukan JSON.") from err
    if isinstance(data.get("error"), dict):
        raise IngestServiceError(
            f"Model AI: {pesan_aman(Exception(str(data['error'].get('message') or 'error')))}"
        )
    choices = data.get("choices") or []
    konten = (choices[0].get("message") or {}).get("content") if choices else None
    if isinstance(konten, list):
        konten = "".join(
            bagian.get("text", "") if isinstance(bagian, dict) else str(bagian)
            for bagian in konten
        )
    if not isinstance(konten, str) or not konten.strip():
        raise IngestServiceError("Model AI tidak mengembalikan konten jawaban.")
    return konten


def _validasi(konten: str) -> ImportPlan | None:
    teks = konten.strip()
    if teks.startswith("```"):
        bagian = teks.split("\n", 1)
        teks = bagian[1] if len(bagian) > 1 else teks
        teks = teks.rsplit("```", 1)[0].strip()
    try:
        data = json.loads(teks)
    except json.JSONDecodeError:
        return None
    try:
        return ImportPlan.model_validate(data)
    except ValidationError:
        return None
