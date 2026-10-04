"""Error dan utilitas bersama untuk pipeline AI import dokumen (ingest)."""
import re


class IngestConfigError(RuntimeError):
    """Konfigurasi layanan AI (kunci API) belum lengkap."""


class IngestServiceError(RuntimeError):
    """Kegagalan dari layanan eksternal atau model pada pipeline ingest."""


_RAHASIA = re.compile(r"(sk-[A-Za-z0-9_\-]+|llx-[A-Za-z0-9_\-]+|Bearer\s+\S+)", re.IGNORECASE)


def pesan_aman(err: Exception, batas: int = 300) -> str:
    """Bersihkan pesan error dari kunci API sebelum dikirim ke klien."""
    teks = str(err)
    teks = _RAHASIA.sub("[disamarkan]", teks)
    teks = " ".join(teks.split())
    return teks[:batas]
