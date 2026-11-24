# AI Journal Hunter 🎯📚
## Intelligent Academic Journal Discovery, Search & Verification System

AI Journal Hunter adalah platform pencarian dan verifikasi jurnal ilmiah otomatis berbasis instruksi bahasa alami (Natural Language Processing). Aplikasi ini mengintegrasikan panen metadata multi-sumber akademik, verifikasi akreditasi nasional SINTA (S1–S6) dan Scopus internasional, generator sitasi otomatis (APA-7, BibTeX, RIS), dan sintesis telaah pustaka (Literature Review) berbasis 15 Model Google Gemini (Gemini 1 hingga Gemini 4).

---

## 🌟 Fitur Utama

1. **Natural Language Query Interpretation**:
   - Menerjemahkan instruksi bahasa Indonesia/Inggris menjadi parameter pencarian terstruktur (topik, sinonim, rentang tahun, filter indeksasi, target SINTA, dsb).
2. **Multi-Source Academic Harvester**:
   - Mengambil artikel ilmiah secara paralel dari CrossRef, OpenAlex, DOAJ, Semantic Scholar, dan Scopus.
   - Dilengkapi deduplikasi berbasis DOI dan kesamaan judul (normalized Levenshtein).
3. **Automated Indexing Verification (SINTA & Scopus)**:
   - Verifikasi status indeksasi jurnal terhadap basis data 25+ jurnal terakreditasi SINTA (S1–S6) dan terindeks Scopus.
   - Akses verifikasi 1-klik ke Scopus Sources resmi, SCImago Journal Rank (SJR Kuartil Q1–Q4), dan SINTA Kemdikbud.
4. **15 Model Google Gemini (Gemini 1–4)**:
   - Dukungan 15 varian model Google Gemini dari generasi 1.5, 2.5, 3.0, 3.1, 3.5, 3.6, 3.7, 3.8, hingga 4.0 Argon.
   - Rotasi otomatis (round-robin failover) melintasi 3 Gemini API Keys untuk ketahanan terhadap rate limit.
5. **Direktori Sumber Akademik & Pusat Verifikasi Scopus**:
   - **10 Mesin Pencari & Repositori**: OpenAlex, Crossref, Unpaywall, DOAJ, Semantic Scholar, CORE, Europe PMC, PubMed Central, arXiv, OpenAIRE.
   - **Otoritas Verifikasi Scopus**: Scopus Sources official, SCImago Journal Rank (SJR), Elsevier Developer Portal.
   - **10 Penerbit Open Access**: PLOS, BioMed Central (BMC), MDPI, Frontiers, Springer Nature, IEEE Xplore, ACM Digital Library, ScienceDirect, Wiley Online Library, Taylor & Francis Online.
6. **AI Literature Review Synthesizer & Deep Abstract Breakdown**:
   - Bedah abstrak instan: Tujuan, Metodologi, Temuan, Implikasi, dan Poin Kunci.
   - Sintesis tinjauan pustaka komprehensif berformat publikasi akademik lengkap dengan sitasi in-text dan daftar pustaka APA-7.
7. **Ekspor & Manajemen Riset**:
   - Ekspor hasil pencarian ke CSV, XLSX, BibTeX, RIS, dan referensi teks APA-7.
   - Manajemen bookmark dan pengelompokan ke dalam Proyek Riset.

---

## 🏛️ Direktori Sumber Akademik & Verifikasi Scopus

### A. 10 Mesin Pencari & Repositori Ilmiah
1. **OpenAlex** (`https://openalex.org/`): Mencari artikel berdasarkan kata kunci & tahun (Graf 250M+ publikasi).
2. **Crossref** (`https://www.crossref.org/`): Registrasi metadata bibliografi dan DOI resmi.
3. **Unpaywall** (`https://unpaywall.org/`): Menemukan lokasi naskah Open Access yang legal & PDF bebas bayar.
4. **DOAJ** (`https://doaj.org/`): Direktori jurnal Open Access terakreditasi internasional bebas predator.
5. **Semantic Scholar** (`https://www.semanticscholar.org/`): Penelusuran cerdas AI & kutipan berpengaruh.
6. **CORE** (`https://core.ac.uk/`): Agregator repositori penelitian dan perpustakaan universitas terbesar.
7. **Europe PMC** (`https://europepmc.org/`): 40M+ artikel sains hayati dan biomedis teks lengkap.
8. **PubMed Central (PMC)** (`https://pmc.ncbi.nlm.nih.gov/`): Arsip naskah digital resmi NIH/NLM.
9. **arXiv** (`https://arxiv.org/`): Repositori pra-cetak komputer, AI, matematika, dan fisika terbuka.
10. **OpenAIRE** (`https://explore.openaire.eu/`): Infrastruktur penelitian terbuka Uni Eropa.

### B. Portal Verifikasi Jurnal Scopus & Kuartil
1. **Scopus Sources** (`https://www.scopus.com/sources`): Portal resmi Elsevier verifikasi indeksasi Scopus & CiteScore.
2. **SCImago Journal & Country Rank (SJR)** (`https://www.scimagojr.com/`): Verifikasi kuartil resmi Q1, Q2, Q3, Q4.
3. **Elsevier Developer Portal** (`https://dev.elsevier.com/`): Dokumentasi dan kunci API institusional Scopus.

### C. 10 Penerbit Open Access Terkemuka
- **PLOS** (`https://plos.org/`) · **BioMed Central (BMC)** (`https://www.biomedcentral.com/`)
- **MDPI** (`https://www.mdpi.com/`) · **Frontiers** (`https://www.frontiersin.org/`)
- **Springer Nature** (`https://link.springer.com/`) · **IEEE Xplore** (`https://ieeexplore.ieee.org/`)
- **ACM Digital Library** (`https://dl.acm.org/`) · **ScienceDirect** (`https://www.sciencedirect.com/`)
- **Wiley Online Library** (`https://onlinelibrary.wiley.com/`) · **Taylor & Francis Online** (`https://www.tandfonline.com/`)

### D. Rekomendasi Alur Otomasi Pencarian Jurnal
`OpenAlex` (Kata Kunci & Tahun) → `Crossref` (DOI & Metadata) → `Unpaywall` (PDF Legal) → `DOAJ` (Akreditasi OA) → `Scopus Sources / SCImago` (Verifikasi Indeks & Kuartil) → `Semantic Scholar & Europe PMC` (Sitasi & Naskah Lengkap) → `CORE & arXiv` (Repositori Global).

---

## 🤖 Daftar 15 Model Gemini Terintegrasi (Gemini 1 – 4)

| No | Model ID | Nama Model | Generasi / Badge | Konteks | Karakteristik Utama |
|---|---|---|---|---|---|
| 1 | `gemini-3.5-flash` | Gemini 3.5 Flash | Gemini 3.5 · Default SOTA Fast | 1M tokens | Kecepatan tinggi dan akurasi tinggi untuk interpretasi instruksi. |
| 2 | `gemini-3.5-flash-lite` | Gemini 3.5 Flash-Lite | Gemini 3.5 · High Efficiency | 1M tokens | Ekstraksi kata kunci dan sinonim instan berbiaya rendah. |
| 3 | `gemini-3-flash-preview` | Gemini 3 Flash Preview | Gemini 3.0 · Next-Gen Multimodal | 1M tokens | Arsitektur multimodal Gemini 3 untuk analisis dokumen. |
| 4 | `gemini-3.1-pro-preview` | Gemini 3.1 Pro Preview | Gemini 3.1 · Frontier Reasoning | 2M tokens | Penalaran ilmiah mendalam untuk sintesis multi-makalah. |
| 5 | `gemini-3.1-flash-lite` | Gemini 3.1 Flash-Lite | Gemini 3.1 · High Throughput | 1M tokens | Pemrosesan batch cepat untuk penilaian abstrak. |
| 6 | `gemini-3.6-flash` | Gemini 3.6 Flash | Gemini 3.6 · SINTA & Citation | 1M tokens | Dioptimalkan untuk verifikasi bibliografi dan standar SINTA. |
| 7 | `gemini-3.7-flash` | Gemini 3.7 Flash | Gemini 3.7 · Logical Deduction | 1M tokens | Deteksi kesenjangan riset (*research gaps*) dan validasi metodologi. |
| 8 | `gemini-3.8-flash` | Gemini 3.8 Flash | Gemini 3.8 · Literature Synthesizer | 1M tokens | Penulisan naskah tinjauan pustaka ilmiah berstandar publikasi. |
| 9 | `gemini-4-argon` | Gemini 4 Argon | Gemini 4.0 · Ultimate Frontier | 2M tokens | Arsitektur riset frontier generasi terbaru dari Google DeepMind. |
| 10 | `gemini-2.5-pro` | Gemini 2.5 Pro | Gemini 2.5 · Deep Reasoning | 2M tokens | Analisis komparatif mendalam antar artikel ilmiah. |
| 11 | `gemini-2.5-flash` | Gemini 2.5 Flash | Gemini 2.5 · High Throughput | 1M tokens | Ekstraksi metadata cepat dengan latensi rendah. |
| 12 | `gemini-2.5-flash-lite` | Gemini 2.5 Flash-Lite | Gemini 2.5 · Efficient | 1M tokens | Parsing query interaktif dengan jejak memori minimal. |
| 13 | `gemini-flash-latest` | Gemini 1.5 Flash (Latest) | Gemini 1.5 · Production Stable | 1M tokens | Endpoint produksi stabil untuk klasifikasi metadata. |
| 14 | `gemini-pro-latest` | Gemini 1.5 Pro (Latest) | Gemini 1.5 · Deep Analysis | 2M tokens | Analisis teks lengkap untuk korpus literatur besar. |
| 15 | `gemini-flash-lite-latest` | Gemini 1.5 Flash-Lite | Gemini 1.5 · Low Latency | 1M tokens | Latensi ultra-rendah untuk saran pencarian cepat. |

---

## 🛠️ Arsitektur & Teknologi

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, HTTPX Async.
- **Database**: Prisma Cloud PostgreSQL (`db.prisma.io:5432`) dengan schema relational lengkap dan failover SQLite offline.
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons, React Hot Toast.
- **AI Engine**: Google Gemini API via 3-Key Multi-rotation Engine + DeepSeek API integration + Fallback Resilient Synthesizer.

---

## 🚀 Panduan Menjalankan Aplikasi Secara Lokal

### 1. Menjalankan Backend API (FastAPI)
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Akses API Documentation:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Redoc: `http://127.0.0.1:8000/redoc`
- Health Status: `http://127.0.0.1:8000/api/health`
- Models Registry: `http://127.0.0.1:8000/api/models`

### 2. Menjalankan Frontend (Vite + React)
```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
Buka peramban di `http://localhost:5173/`

---

## 📌 Konfigurasi Lingkungan (`backend/.env`)

```ini
APP_ENV=development
DATABASE_URL=postgresql://user:password@localhost:5432/journal_hunter
SQLITE_FALLBACK_URL=sqlite:///./journal_hunter.db

# Google Gemini Multi-Key Rotation
AI_PROVIDER=gemini
DEFAULT_MODEL=gemini-3.5-flash
GEMINI_API_KEY=your_gemini_api_key_1
GEMINI_API_KEY_2=your_gemini_api_key_2
GEMINI_API_KEY_3=your_gemini_api_key_3

# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key

# Academic Search APIs
CROSSREF_EMAIL=user@journalhunter.app
APP_CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
```
