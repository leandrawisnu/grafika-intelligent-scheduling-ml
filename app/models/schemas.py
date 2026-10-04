from pydantic import BaseModel
from typing import Optional


class SlotML(BaseModel):
    id: str
    class_name: str = ""
    subject: str = ""
    day: str = ""
    time_slot: str = ""
    room: str = ""
    teacher: str = ""
    week_number: int = 1


class TeacherML(BaseModel):
    id: str
    name: str
    max_daily_hours: float = 8.0
    off_days: list[str] = []
    subjects: list[str] = []


class PredictRequest(BaseModel):
    schedule_id: str
    slots: list[SlotML]
    teachers: list[TeacherML]


class MLConflict(BaseModel):
    type: str
    severity: str
    description: str
    slot_ids: list[str] = []
    confidence: float = 1.0


class PredictResponse(BaseModel):
    conflicts: list[MLConflict]


class ResolveRequest(BaseModel):
    conflict_id: str
    context: dict


class Alternative(BaseModel):
    rank: int
    confidence: float
    changes: list[dict]
    explanation: str


class ResolveResponse(BaseModel):
    alternatives: list[Alternative]


class ExplainRequest(BaseModel):
    conflict_id: str
    context: dict


class ExplainResponse(BaseModel):
    explanation: str
    reasoning_steps: list[str] = []


class QueryRequest(BaseModel):
    query: str
    schedule_id: str


class QueryResponse(BaseModel):
    answer: str
    result_data: Optional[dict] = None


class BarisJadwalEkstrak(BaseModel):
    hari: str = ""
    jam: str = ""
    mata_pelajaran: str = ""
    kelas: str = ""
    guru: str = ""
    ruangan: str = ""


class EkstrakJadwalResponse(BaseModel):
    baris: list[BarisJadwalEkstrak]


# ---- AI Import dokumen (ingest) ----

class IngestParseResponse(BaseModel):
    markdown: str = ""
    teks: str = ""
    jumlah_halaman: int = 0
    peringatan: list[str] = []


class MasterGuruUsulan(BaseModel):
    ref: str
    nama: str
    nip: Optional[str] = None
    aksi: str = "buat"


class MasterMapelUsulan(BaseModel):
    ref: str
    nama: str
    kode: Optional[str] = None
    jam_wajib_per_minggu: Optional[float] = None
    tingkat: Optional[int] = None
    aksi: str = "buat"


class MasterRuanganUsulan(BaseModel):
    ref: str
    nama: str
    kode: Optional[str] = None
    tipe_ruangan: Optional[str] = None
    kapasitas: Optional[int] = None
    aksi: str = "buat"


class MasterKelasUsulan(BaseModel):
    ref: str
    nama: str
    kode: Optional[str] = None
    tingkat: Optional[int] = None
    jurusan_id: Optional[str] = None
    jurusan_ref: Optional[str] = None
    aksi: str = "buat"


class MasterJurusanUsulan(BaseModel):
    ref: str
    nama: str
    kode: Optional[str] = None
    aksi: str = "buat"


class MasterUsulan(BaseModel):
    guru: list[MasterGuruUsulan] = []
    mata_pelajaran: list[MasterMapelUsulan] = []
    ruangan: list[MasterRuanganUsulan] = []
    kelas: list[MasterKelasUsulan] = []
    jurusan: list[MasterJurusanUsulan] = []


class BarisJadwalPlan(BaseModel):
    hari: str = ""
    jam: str = ""
    kelas: str = ""
    mata_pelajaran: str = ""
    guru: str = ""
    ruangan: str = ""
    hari_id: Optional[str] = None
    jam_pelajaran_id: Optional[str] = None
    kelas_id: Optional[str] = None
    mata_pelajaran_id: Optional[str] = None
    guru_id: Optional[str] = None
    ruangan_id: Optional[str] = None
    kelas_ref: Optional[str] = None
    mapel_ref: Optional[str] = None
    guru_ref: Optional[str] = None
    ruangan_ref: Optional[str] = None
    status: str = "perlu_pilihan"
    keyakinan: float = 0.0
    catatan: str = ""


class ImportPlan(BaseModel):
    jenis_dokumen: str = "tidak_dikenali"
    ringkasan: str = ""
    keyakinan: float = 0.0
    peringatan: list[str] = []
    master_usulan: MasterUsulan = MasterUsulan()
    baris_jadwal: list[BarisJadwalPlan] = []


class IngestMapRequest(BaseModel):
    teks: str
    konteks: dict = {}
