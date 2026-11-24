"""Journal verification service for SINTA and Scopus indexing."""
from __future__ import annotations
import re
import html
import unicodedata
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from ..models.models import Journal, Article, VerificationStatus, IndexingVerification
from .scimago_verifier import verify_journal_scimago, analyze_scimago_status

logger = logging.getLogger(__name__)

# Curated reference database of verified SINTA and Scopus indexed journals.
# Multidisciplinary: Computer Science, Economics/Accounting, Health/Medicine, Education, Engineering, and Law.
KNOWN_JOURNALS: List[Dict[str, Any]] = [
    # =========================================================================
    # --- SINTA 1 & SCOPUS (Top-Tier Indonesian Scientific Journals) ---
    # =========================================================================
    {
        "name": "TELKOMNIKA (Telecommunication Computing Electronics and Control)",
        "aliases": ["telkomnika", "telkomnika telecommunication computing electronics and control"],
        "issn": "1693-6930",
        "eissn": "2302-9293",
        "publisher": "Universitas Ahmad Dahlan",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2011,
        "scopus_coverage_end": None,
        "sinta_id": "60",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/60",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100201509",
        "is_open_access": True,
    },
    {
        "name": "International Journal of Electrical and Computer Engineering (IJECE)",
        "aliases": ["ijece", "international journal of electrical and computer engineering"],
        "issn": "2088-8708",
        "eissn": "2722-2578",
        "publisher": "Institute of Advanced Engineering and Science (IAES)",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2012,
        "scopus_coverage_end": None,
        "sinta_id": "65",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/65",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100382424",
        "is_open_access": True,
    },
    {
        "name": "Bulletin of Electrical Engineering and Informatics",
        "aliases": ["beei", "bulletin of electrical engineering and informatics"],
        "issn": "2089-3191",
        "eissn": "2302-9285",
        "publisher": "Universitas Ahmad Dahlan & IAES",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2018,
        "scopus_coverage_end": None,
        "sinta_id": "83",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/83",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100829158",
        "is_open_access": True,
    },
    {
        "name": "Journal of ICT Research and Applications",
        "aliases": ["jictra", "journal of ict research and applications"],
        "issn": "2337-5787",
        "eissn": "2338-5499",
        "publisher": "Institut Teknologi Bandung (ITB)",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2013,
        "scopus_coverage_end": None,
        "sinta_id": "102",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/102",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100287114",
        "is_open_access": True,
    },
    {
        "name": "Indonesian Journal of Science and Technology",
        "aliases": ["ijst", "indonesian journal of science and technology"],
        "issn": "2528-1410",
        "eissn": "2527-8045",
        "publisher": "Universitas Pendidikan Indonesia",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2016,
        "scopus_coverage_end": None,
        "sinta_id": "180",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/180",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100880133",
        "is_open_access": True,
    },
    {
        "name": "International Journal on Advanced Science, Engineering and Information Technology (IJASEIT)",
        "aliases": ["ijaseit", "international journal on advanced science engineering and information technology"],
        "issn": "2088-5334",
        "eissn": "2460-6952",
        "publisher": "INSIS",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2015,
        "scopus_coverage_end": None,
        "sinta_id": "71",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/71",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100417937",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Akuntansi dan Keuangan Indonesia (JAKI)",
        "aliases": ["jaki", "jurnal akuntansi dan keuangan indonesia", "jurnal akuntansi & keuangan indonesia"],
        "issn": "1829-8494",
        "eissn": "2406-9701",
        "publisher": "Fakultas Ekonomi dan Bisnis Universitas Indonesia",
        "sinta_rank": 1,
        "is_scopus_indexed": False,
        "sinta_id": "18",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/18",
        "is_open_access": True,
    },
    {
        "name": "Gadjah Mada International Journal of Business",
        "aliases": ["gama ijb", "gamaijb", "gadjah mada international journal of business"],
        "issn": "1411-1128",
        "eissn": "2338-7238",
        "publisher": "Universitas Gadjah Mada",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2013,
        "scopus_coverage_end": None,
        "sinta_id": "12",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/12",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100236814",
        "is_open_access": True,
    },
    {
        "name": "Journal of Indonesian Economy and Business",
        "aliases": ["jieb", "journal of indonesian economy and business"],
        "issn": "2085-8272",
        "eissn": "2338-5847",
        "publisher": "Universitas Gadjah Mada",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2019,
        "scopus_coverage_end": None,
        "sinta_id": "13",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/13",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100936173",
        "is_open_access": True,
    },
    {
        "name": "Acta Medica Indonesiana",
        "aliases": ["acta medica indonesiana", "acta med indones"],
        "issn": "0125-9326",
        "eissn": "2338-2732",
        "publisher": "Indonesian Society of Internal Medicine / FKUI",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2004,
        "scopus_coverage_end": None,
        "sinta_id": "2",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/2",
        "scopus_source_url": "https://www.scopus.com/sourceid/4700152402",
        "is_open_access": True,
    },
    {
        "name": "Medical Journal of Indonesia",
        "aliases": ["mji", "medical journal of indonesia", "med j indones"],
        "issn": "0853-1773",
        "eissn": "2252-8083",
        "publisher": "Faculty of Medicine Universitas Indonesia",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2012,
        "scopus_coverage_end": None,
        "sinta_id": "4",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/4",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100234024",
        "is_open_access": True,
    },
    {
        "name": "HAYATI Journal of Biosciences",
        "aliases": ["hayati", "hayati journal of biosciences", "hayati j biosci"],
        "issn": "1978-3019",
        "eissn": "2086-4094",
        "publisher": "Institut Pertanian Bogor (IPB)",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2007,
        "scopus_coverage_end": None,
        "sinta_id": "22",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/22",
        "scopus_source_url": "https://www.scopus.com/sourceid/19400157125",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Pendidikan IPA Indonesia",
        "aliases": ["jpii", "jurnal pendidikan ipa indonesia"],
        "issn": "2252-6935",
        "eissn": "2339-1286",
        "publisher": "Universitas Negeri Semarang (UNNES)",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2017,
        "scopus_coverage_end": None,
        "sinta_id": "45",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/45",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100824905",
        "is_open_access": True,
    },
    {
        "name": "Studies in English Language and Education",
        "aliases": ["siele", "studies in english language and education"],
        "issn": "2355-2794",
        "eissn": "2461-0275",
        "publisher": "Universitas Syiah Kuala (USK)",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2020,
        "scopus_coverage_end": None,
        "sinta_id": "95",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/95",
        "scopus_source_url": "https://www.scopus.com/sourceid/21101019688",
        "is_open_access": True,
    },
    {
        "name": "Cakrawala Pendidikan: Jurnal Ilmiah Pendidikan",
        "aliases": ["cakrawala pendidikan", "jurnal cakrawala pendidikan"],
        "issn": "0216-1370",
        "eissn": "2442-8620",
        "publisher": "Universitas Negeri Yogyakarta (UNY)",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2019,
        "scopus_coverage_end": None,
        "sinta_id": "52",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/52",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100918731",
        "is_open_access": True,
    },
    {
        "name": "Hasanuddin Law Review",
        "aliases": ["halrev", "hasanuddin law review"],
        "issn": "2442-9880",
        "eissn": "2442-9899",
        "publisher": "Universitas Hasanuddin",
        "sinta_rank": 1,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2018,
        "scopus_coverage_end": None,
        "sinta_id": "88",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/88",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100936171",
        "is_open_access": True,
    },

    # =========================================================================
    # --- SINTA 2 (Highly Accredited National Scientific Journals) ---
    # =========================================================================
    # --- Akuntansi, Bisnis, Keuangan & Manajemen ---
    {
        "name": "E-Jurnal Akuntansi",
        "aliases": ["e-jurnal akuntansi", "e jurnal akuntansi", "e-jurnal akuntansi universitas udayana", "e jurnal akuntansi udayana"],
        "issn": "2302-8556",
        "eissn": "2302-8556",
        "publisher": "Universitas Udayana",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "772",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/772",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Riset Akuntansi dan Keuangan",
        "aliases": ["jrak", "jurnal riset akuntansi dan keuangan", "jurnal riset akuntansi & keuangan", "jrak upi"],
        "issn": "2338-1507",
        "eissn": "2541-061X",
        "publisher": "Universitas Pendidikan Indonesia",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "1845",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/1845",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Akuntansi Profesi",
        "aliases": ["jurnal akuntansi profesi", "jurnal akuntansi profesi undiksha", "jap undiksha"],
        "issn": "2338-6177",
        "eissn": "2686-2468",
        "publisher": "Universitas Pendidikan Ganesha",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "2134",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/2134",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Dinamika Akuntansi dan Bisnis",
        "aliases": ["jdab", "jurnal dinamika akuntansi dan bisnis", "jdab usk"],
        "issn": "2355-9462",
        "eissn": "2528-1143",
        "publisher": "Universitas Syiah Kuala",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "1923",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/1923",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Dinamika Akuntansi",
        "aliases": ["jda", "jurnal dinamika akuntansi", "jda unnes"],
        "issn": "2085-4277",
        "eissn": "2502-6224",
        "publisher": "Universitas Negeri Semarang",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "1104",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/1104",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Akuntansi dan Auditing Indonesia",
        "aliases": ["jaai", "jurnal akuntansi dan auditing indonesia", "jaai uii"],
        "issn": "1410-2420",
        "eissn": "2528-6528",
        "publisher": "Universitas Islam Indonesia",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "890",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/890",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Akuntansi dan Keuangan",
        "aliases": ["jak petra", "jurnal akuntansi dan keuangan", "jak"],
        "issn": "1411-0288",
        "eissn": "2338-8137",
        "publisher": "Universitas Kristen Petra",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "670",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/670",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Akuntansi Multiparadigma",
        "aliases": ["jamal", "jurnal akuntansi multiparadigma", "jamal ub"],
        "issn": "2086-7603",
        "eissn": "2089-5879",
        "publisher": "Universitas Brawijaya",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "620",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/620",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Bisnis dan Akuntansi",
        "aliases": ["jba", "jurnal bisnis dan akuntansi", "jba trisakti"],
        "issn": "1410-9875",
        "eissn": "2580-4944",
        "publisher": "Trisakti School of Management",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "1412",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/1412",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Benefita",
        "aliases": ["jurnal benefita", "benefita", "jurnal benefita: ekonomi pembangunan, manajemen bisnis & akuntansi"],
        "issn": "2477-7862",
        "eissn": "2477-7862",
        "publisher": "LLDIKTI Wilayah X",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "2781",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/2781",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Wira Ekonomi Mikroskil",
        "aliases": ["jurnal wira ekonomi mikroskil", "wira ekonomi mikroskil", "jwem"],
        "issn": "2088-5180",
        "eissn": "2407-1609",
        "publisher": "Universitas Mikroskil",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "3122",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/3122",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Ilmiah Akuntansi dan Bisnis",
        "aliases": ["jiab", "jurnal ilmiah akuntansi dan bisnis", "jiab udayana"],
        "issn": "2302-514X",
        "eissn": "2303-1018",
        "publisher": "Universitas Udayana",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "1520",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/1520",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Akuntansi dan Investasi",
        "aliases": ["jai", "jurnal akuntansi dan investasi", "jai umy"],
        "issn": "2622-3899",
        "eissn": "2622-6413",
        "publisher": "Universitas Muhammadiyah Yogyakarta",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "1650",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/1650",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Keuangan dan Perbankan",
        "aliases": ["jkp", "jurnal keuangan dan perbankan", "jkp unmer"],
        "issn": "1410-8089",
        "eissn": "2443-2687",
        "publisher": "Universitas Merdeka Malang",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "780",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/780",
        "is_open_access": True,
    },
    # --- Ilmu Komputer, Informatika & Sistem Informasi ---
    {
        "name": "Jurnal RESTI (Rekayasa Sistem dan Teknologi Informasi)",
        "aliases": ["resti", "jurnal resti", "rekayasa sistem dan teknologi informasi"],
        "issn": "2580-0760",
        "eissn": "2580-0760",
        "publisher": "Ikatan Ahli Informatika Indonesia (IAII)",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "2858",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/2858",
        "is_open_access": True,
    },
    {
        "name": "JUTI: Jurnal Ilmiah Teknologi Informasi",
        "aliases": ["juti", "jurnal ilmiah teknologi informasi", "juti its"],
        "issn": "1412-6524",
        "eissn": "2407-0904",
        "publisher": "Institut Teknologi Sepuluh Nopember (ITS)",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "1214",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/1214",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Ilmu Komputer dan Informasi (JIKI)",
        "aliases": ["jiki", "jurnal ilmu komputer dan informasi", "jiki ui"],
        "issn": "2085-1510",
        "eissn": "2502-9274",
        "publisher": "Fakultas Ilmu Komputer Universitas Indonesia",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "764",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/764",
        "is_open_access": True,
    },
    {
        "name": "JATISI (Jurnal Teknik Informatika dan Sistem Informasi)",
        "aliases": ["jatisi", "jurnal teknik informatika dan sistem informasi", "jatisi mikroskil"],
        "issn": "2407-4322",
        "eissn": "2503-2933",
        "publisher": "Universitas Mikroskil",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "2980",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/2980",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Nasional Pendidikan Teknik Informatika (JANAPATI)",
        "aliases": ["janapati", "jurnal nasional pendidikan teknik informatika"],
        "issn": "2089-8673",
        "eissn": "2548-4265",
        "publisher": "Universitas Pendidikan Ganesha",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "2240",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/2240",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Teknologi Informasi dan Ilmu Komputer (JTIIK)",
        "aliases": ["jtiik", "jurnal teknologi informasi dan ilmu komputer", "jtiik ub"],
        "issn": "2355-7699",
        "eissn": "2528-6579",
        "publisher": "Universitas Brawijaya",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "1738",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/1738",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Sistem Informasi Bisnis (JSINBIS)",
        "aliases": ["jsinbis", "jurnal sistem informasi bisnis", "jsinbis undip"],
        "issn": "2088-3587",
        "eissn": "2502-2377",
        "publisher": "Universitas Diponegoro",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "1450",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/1450",
        "is_open_access": True,
    },
    {
        "name": "Kursor: Jurnal Studi Biomedis, Rekayasa Sistem, dan Komputasi",
        "aliases": ["kursor", "jurnal kursor"],
        "issn": "0216-0544",
        "eissn": "2502-0579",
        "publisher": "Universitas Trunojoyo Madura",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "988",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/988",
        "is_open_access": True,
    },
    {
        "name": "ILKOM Jurnal Ilmiah",
        "aliases": ["ilkom jurnal ilmiah", "ilkom", "jurnal ilmiah ilkom"],
        "issn": "2087-1716",
        "eissn": "2548-7779",
        "publisher": "Universitas Muslim Indonesia",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "2340",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/2340",
        "is_open_access": True,
    },
    # --- Kesehatan, Kedokteran & Sains Hayati ---
    {
        "name": "Kesmas: Jurnal Kesehatan Masyarakat Nasional",
        "aliases": ["kesmas", "kesmas: national public health journal", "jurnal kesehatan masyarakat nasional"],
        "issn": "1907-7505",
        "eissn": "2460-0601",
        "publisher": "Fakultas Kesehatan Masyarakat Universitas Indonesia",
        "sinta_rank": 2,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2017,
        "scopus_coverage_end": None,
        "sinta_id": "8",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/8",
        "scopus_source_url": "https://www.scopus.com/sourceid/21100854443",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Kesehatan Masyarakat (KEMAS)",
        "aliases": ["kemas", "jurnal kesehatan masyarakat kemas", "kemas unnes"],
        "issn": "1858-1196",
        "eissn": "2355-3596",
        "publisher": "Universitas Negeri Semarang",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "1120",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/1120",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Keperawatan Indonesia",
        "aliases": ["jki ui", "jurnal keperawatan indonesia"],
        "issn": "1410-4490",
        "eissn": "2354-9203",
        "publisher": "Fakultas Ilmu Keperawatan Universitas Indonesia",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "512",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/512",
        "is_open_access": True,
    },
    # --- Pendidikan, Hukum & Humaniora ---
    {
        "name": "Jurnal Pendidikan Vokasi",
        "aliases": ["jpv", "jurnal pendidikan vokasi", "jpv uny"],
        "issn": "2088-2866",
        "eissn": "2476-9401",
        "publisher": "Universitas Negeri Yogyakarta",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "420",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/420",
        "is_open_access": True,
    },
    {
        "name": "Mimbar Hukum",
        "aliases": ["mimbar hukum", "mimbar hukum fakultas hukum ugm", "mimbar hukum ugm"],
        "issn": "0852-100X",
        "eissn": "2443-0994",
        "publisher": "Fakultas Hukum Universitas Gadjah Mada",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "310",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/310",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Hukum & Pembangunan",
        "aliases": ["jurnal hukum & pembangunan", "jurnal hukum dan pembangunan", "jhp ui"],
        "issn": "0125-9687",
        "eissn": "2503-1465",
        "publisher": "Fakultas Hukum Universitas Indonesia",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "sinta_id": "290",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/290",
        "is_open_access": True,
    },

    # =========================================================================
    # --- SINTA 3 (Recognized National Scientific Journals) ---
    # =========================================================================
    {
        "name": "Eqien - Jurnal Ekonomi dan Bisnis",
        "aliases": ["eqien", "eqien - jurnal ekonomi dan bisnis", "eqien jurnal ekonomi dan bisnis"],
        "issn": "2503-4448",
        "eissn": "2654-5837",
        "publisher": "STIE Banten",
        "sinta_rank": 3,
        "is_scopus_indexed": False,
        "sinta_id": "4810",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/4810",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Informatika: Jurnal Pengembangan IT (JPIT)",
        "aliases": ["jpit", "jurnal pengembangan it"],
        "issn": "2477-5126",
        "eissn": "2548-9356",
        "publisher": "Institut Teknologi Telkom Purwokerto",
        "sinta_rank": 3,
        "is_scopus_indexed": False,
        "sinta_id": "3120",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/3120",
        "is_open_access": True,
    },
    {
        "name": "Ultima InfoSys : Jurnal Ilmu Sistem Informasi",
        "aliases": ["ultima infosys", "ultima infosys : jurnal ilmu sistem informasi"],
        "issn": "2085-4609",
        "eissn": "2549-4015",
        "publisher": "Universitas Multimedia Nusantara",
        "sinta_rank": 3,
        "is_scopus_indexed": False,
        "sinta_id": "3890",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/3890",
        "is_open_access": True,
    },
    {
        "name": "Infotek: Jurnal Informatika dan Teknologi",
        "aliases": ["infotek", "infotek: jurnal informatika dan teknologi"],
        "issn": "2614-8773",
        "eissn": "2614-8773",
        "publisher": "Universitas Hamzanwadi",
        "sinta_rank": 3,
        "is_scopus_indexed": False,
        "sinta_id": "4210",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/4210",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Ilmiah Akuntansi dan Keuangan (JIAK)",
        "aliases": ["jiak", "jurnal ilmiah akuntansi dan keuangan"],
        "issn": "2622-2191",
        "eissn": "2622-2205",
        "publisher": "STIE Widya Manggala",
        "sinta_rank": 3,
        "is_scopus_indexed": False,
        "sinta_id": "4560",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/4560",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Riset Akuntansi Mercu Buana",
        "aliases": ["jramb", "jurnal riset akuntansi mercu buana"],
        "issn": "2460-1233",
        "eissn": "2621-3168",
        "publisher": "Universitas Mercu Buana",
        "sinta_rank": 3,
        "is_scopus_indexed": False,
        "sinta_id": "4180",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/4180",
        "is_open_access": True,
    },
    {
        "name": "JAKPI - Jurnal Akuntansi, Keuangan & Perpajakan Indonesia",
        "aliases": ["jakpi", "jurnal akuntansi keuangan perpajakan indonesia"],
        "issn": "2338-8927",
        "eissn": "2685-6182",
        "publisher": "Universitas Tadulako",
        "sinta_rank": 3,
        "is_scopus_indexed": False,
        "sinta_id": "4320",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/4320",
        "is_open_access": True,
    },
    {
        "name": "Al-Kharaj: Jurnal Ekonomi, Keuangan & Bisnis Syariah",
        "aliases": ["al-kharaj", "al kharaj"],
        "issn": "2715-0011",
        "eissn": "2715-0321",
        "publisher": "STEI SEBI",
        "sinta_rank": 3,
        "is_scopus_indexed": False,
        "sinta_id": "4950",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/4950",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Proaksi",
        "aliases": ["jurnal proaksi", "proaksi"],
        "issn": "2089-127X",
        "eissn": "2685-9750",
        "publisher": "Universitas Swadaya Gunung Jati",
        "sinta_rank": 3,
        "is_scopus_indexed": False,
        "sinta_id": "3712",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/3712",
        "is_open_access": True,
    },

    # =========================================================================
    # --- SINTA 4 ---
    # =========================================================================
    {
        "name": "Jurnal Ilmiah Komputasi",
        "aliases": ["jurnal ilmiah komputasi"],
        "issn": "1412-9434",
        "eissn": "2549-8479",
        "publisher": "Universitas Trisakti",
        "sinta_rank": 4,
        "is_scopus_indexed": False,
        "sinta_id": "4521",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/4521",
        "is_open_access": True,
    },
    {
        "name": "Jurnal Sistem Komputer dan Kecerdasan Buatan",
        "aliases": ["jurnal sistem komputer dan kecerdasan buatan"],
        "issn": "2620-3022",
        "eissn": "2620-3030",
        "publisher": "Universitas Gunadarma",
        "sinta_rank": 4,
        "is_scopus_indexed": False,
        "sinta_id": "5120",
        "sinta_profile_url": "https://sinta.kemdikbud.go.id/journals/profile/5120",
        "is_open_access": True,
    },
    {
        "name": "MALCOM: Indonesian Journal of Machine Learning and Computer Science",
        "aliases": ["malcom", "indonesian journal of machine learning and computer science"],
        "issn": "2797-2313",
        "eissn": "2775-8575",
        "publisher": "Yayasan Riset dan Inovasi Komputer",
        "sinta_rank": 3,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },
    {
        "name": "LOFIAN: Jurnal Teknologi Informasi dan Komunikasi",
        "aliases": ["lofian", "jurnal teknologi informasi dan komunikasi lofian"],
        "issn": "2798-1002",
        "eissn": "2798-1010",
        "publisher": "Universitas Terbuka",
        "sinta_rank": 4,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },
    {
        "name": "POSTULAT",
        "aliases": ["postulat", "postulat: jurnal hukum dan kriminologi"],
        "issn": "2776-8805",
        "eissn": "2776-8813",
        "publisher": "Fakultas Hukum Universitas",
        "sinta_rank": 4,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },
    {
        "name": "Consensus : Jurnal Ilmu Hukum",
        "aliases": ["consensus", "consensus jurnal ilmu hukum", "jurnal ilmu hukum consensus"],
        "issn": "2774-8840",
        "eissn": "2774-8859",
        "publisher": "Universitas",
        "sinta_rank": 4,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },
    {
        "name": "Improvement: Jurnal Manajemen dan Bisnis",
        "aliases": ["improvement", "improvement jurnal manajemen dan bisnis"],
        "issn": "2808-1129",
        "eissn": "2808-1137",
        "publisher": "Universitas",
        "sinta_rank": 4,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },
    {
        "name": "Buletin Ilmiah Informatika Teknologi",
        "aliases": ["biit", "buletin ilmiah informatika teknologi"],
        "issn": "2828-0911",
        "eissn": "2828-092X",
        "publisher": "Universitas",
        "sinta_rank": 4,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },
    {
        "name": "Bandung Conference Series: Law Studies",
        "aliases": ["bandung conference series law studies", "bcs law studies"],
        "issn": "2828-2124",
        "eissn": "2828-2132",
        "publisher": "Universitas Islam Bandung",
        "sinta_rank": 4,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },
    {
        "name": "Jurnal Teknologi Informasi dan Ilmu Komputer (JTIIK)",
        "aliases": ["jtiik", "jurnal teknologi informasi dan ilmu komputer"],
        "issn": "2355-7699",
        "eissn": "2528-6579",
        "publisher": "Fakultas Ilmu Komputer Universitas Brawijaya",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },
    {
        "name": "Jurnal Edukasi dan Penelitian Informatika (JEPIN)",
        "aliases": ["jepin", "jurnal edukasi dan penelitian informatika"],
        "issn": "2460-0741",
        "eissn": "2548-9364",
        "publisher": "Universitas Tanjungpura",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },
    {
        "name": "Jurnal Infotel",
        "aliases": ["infotel", "jurnal infotel"],
        "issn": "2085-3688",
        "eissn": "2460-0997",
        "publisher": "Institut Teknologi Telkom Purwokerto",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },
    {
        "name": "Jurnal Matrik",
        "aliases": ["matrik", "matrik : jurnal manajemen, teknik informatika dan rekayasa komputer"],
        "issn": "1858-4144",
        "eissn": "2476-9843",
        "publisher": "Universitas Bumigora",
        "sinta_rank": 2,
        "is_scopus_indexed": True,
        "is_open_access": True,
    },
    {
        "name": "Jurnal SISFOKOM (Sistem Informasi dan Komputer)",
        "aliases": ["sisfokom", "jurnal sisfokom"],
        "issn": "2301-7988",
        "eissn": "2581-0588",
        "publisher": "Universitas Bina Darma",
        "sinta_rank": 3,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },
    {
        "name": "Jurnal Riset Akuntansi & Keuangan",
        "aliases": ["jrak", "jurnal riset akuntansi dan keuangan", "jurnal riset akuntansi & keuangan"],
        "issn": "2338-1507",
        "eissn": "2541-061X",
        "publisher": "Universitas Pendidikan Indonesia",
        "sinta_rank": 2,
        "is_scopus_indexed": False,
        "is_open_access": True,
    },

    # =========================================================================
    # --- Leading International Scopus Journals ---
    # =========================================================================
    {
        "name": "IEEE Access",
        "aliases": ["ieee access"],
        "issn": "2169-3536",
        "eissn": "2169-3536",
        "publisher": "IEEE",
        "sinta_rank": None,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2013,
        "scopus_coverage_end": None,
        "scopus_source_url": "https://www.scopus.com/sourceid/21100374601",
        "is_open_access": True,
    },
    {
        "name": "Nature Communications",
        "aliases": ["nature communications", "nat commun"],
        "issn": "2041-1723",
        "eissn": "2041-1723",
        "publisher": "Nature Publishing Group",
        "sinta_rank": None,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2010,
        "scopus_coverage_end": None,
        "scopus_source_url": "https://www.scopus.com/sourceid/19700182758",
        "is_open_access": True,
    },
    {
        "name": "PLOS ONE",
        "aliases": ["plos one", "plos 1"],
        "issn": "1932-6203",
        "eissn": "1932-6203",
        "publisher": "Public Library of Science",
        "sinta_rank": None,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 2006,
        "scopus_coverage_end": None,
        "scopus_source_url": "https://www.scopus.com/sourceid/10600153309",
        "is_open_access": True,
    },
    {
        "name": "ACM Computing Surveys",
        "aliases": ["acm computing surveys"],
        "issn": "0360-0300",
        "eissn": "1557-7341",
        "publisher": "Association for Computing Machinery",
        "sinta_rank": None,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 1969,
        "scopus_coverage_end": None,
        "scopus_source_url": "https://www.scopus.com/sourceid/28551",
        "is_open_access": False,
    },
    {
        "name": "Artificial Intelligence Review",
        "aliases": ["artificial intelligence review"],
        "issn": "0269-2821",
        "eissn": "1573-7462",
        "publisher": "Springer",
        "sinta_rank": None,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 1986,
        "scopus_coverage_end": None,
        "scopus_source_url": "https://www.scopus.com/sourceid/20857",
        "is_open_access": False,
    },
    {
        "name": "Expert Systems with Applications",
        "aliases": ["expert systems with applications"],
        "issn": "0957-4174",
        "eissn": "1873-6793",
        "publisher": "Elsevier",
        "sinta_rank": None,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 1990,
        "scopus_coverage_end": None,
        "scopus_source_url": "https://www.scopus.com/sourceid/23820",
        "is_open_access": False,
    },
    {
        "name": "Computers & Security",
        "aliases": ["computers & security", "computers and security"],
        "issn": "0167-4048",
        "eissn": "1872-6208",
        "publisher": "Elsevier",
        "sinta_rank": None,
        "is_scopus_indexed": True,
        "scopus_coverage_start": 1982,
        "scopus_coverage_end": None,
        "scopus_source_url": "https://www.scopus.com/sourceid/20658",
        "is_open_access": False,
    },
]


def normalize_string(val: Optional[str]) -> str:
    """Normalize string for fuzzy comparison."""
    if not val:
        return ""
    text = html.unescape(val)
    text = unicodedata.normalize("NFKD", text.lower())
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _match_known_journal(
    norm_target: str,
    issn: Optional[str] = None,
    eissn: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Match against curated KNOWN_JOURNALS by ISSN, name, or aliases."""
    clean_issn = (issn or "").replace("-", "").strip().lower()
    clean_eissn = (eissn or "").replace("-", "").strip().lower()

    for ref in KNOWN_JOURNALS:
        # 1. ISSN match
        ref_issn = (ref.get("issn") or "").replace("-", "").strip().lower()
        ref_eissn = (ref.get("eissn") or "").replace("-", "").strip().lower()
        if clean_issn and (clean_issn == ref_issn or clean_issn == ref_eissn):
            return ref
        if clean_eissn and (clean_eissn == ref_issn or clean_eissn == ref_eissn):
            return ref

        # 2. Normalized primary name match
        norm_ref = normalize_string(ref["name"])
        if norm_ref == norm_target:
            return ref
        if len(norm_target) >= 6 and (norm_target in norm_ref or norm_ref in norm_target):
            return ref

        # 3. Aliases match
        aliases = ref.get("aliases", [])
        for alias in aliases:
            norm_alias = normalize_string(alias)
            if norm_alias == norm_target:
                return ref
            if len(norm_target) >= 5 and (norm_target in norm_alias or norm_alias in norm_target):
                return ref

    return None


def sync_curated_journals(db: Session) -> None:
    """
    Synchronize the database with the authoritative curated KNOWN_JOURNALS list.
    Inserts missing reference journals and corrects any stale/heuristically misclassified ranks.
    """
    logger.info("Synchronizing curated reference SINTA and Scopus journals...")
    for j_data in KNOWN_JOURNALS:
        norm_name = normalize_string(j_data["name"])
        existing = None

        # Try find by exact name
        existing = db.query(Journal).filter(Journal.name == j_data["name"]).first()
        if not existing:
            # Try fuzzy match in DB
            for candidate in db.query(Journal).all():
                if normalize_string(candidate.name) == norm_name:
                    existing = candidate
                    break

        # Check SCImago
        sjr_data = verify_journal_scimago(j_data["name"], j_data.get("issn"), j_data.get("eissn"))
        scim_q = sjr_data.get("scimago_quartile") if sjr_data else None
        scim_sjr = sjr_data.get("sjr_score") if sjr_data else None
        scim_url = sjr_data.get("scimago_url") if sjr_data else j_data.get("scopus_source_url")
        scim_h = sjr_data.get("h_index") if sjr_data else None

        if existing:
            # Correct any mismatch
            updated = False
            if existing.sinta_rank != j_data.get("sinta_rank"):
                existing.sinta_rank = j_data.get("sinta_rank")
                updated = True
            if existing.is_scopus_indexed != j_data.get("is_scopus_indexed", False):
                existing.is_scopus_indexed = j_data.get("is_scopus_indexed", False)
                updated = True
            if scim_q and existing.scimago_quartile != scim_q:
                existing.scimago_quartile = scim_q
                updated = True
            if scim_sjr and existing.sjr_score != scim_sjr:
                existing.sjr_score = scim_sjr
                updated = True
            if scim_url and not existing.scimago_url:
                existing.scimago_url = scim_url
                updated = True
            if scim_h and not existing.h_index:
                existing.h_index = scim_h
                updated = True
            if j_data.get("sinta_id") and not existing.sinta_id:
                existing.sinta_id = j_data.get("sinta_id")
                updated = True
            if j_data.get("sinta_profile_url") and not existing.sinta_profile_url:
                existing.sinta_profile_url = j_data.get("sinta_profile_url")
                updated = True
            if j_data.get("scopus_source_url") and not existing.scopus_source_url:
                existing.scopus_source_url = j_data.get("scopus_source_url")
                updated = True
            if updated:
                existing.verification_source = "curated_database"
                existing.verified_at = datetime.now(timezone.utc)
        else:
            # Insert fresh
            journal = Journal(
                name=j_data["name"],
                issn=j_data.get("issn"),
                eissn=j_data.get("eissn"),
                publisher=j_data.get("publisher"),
                sinta_rank=j_data.get("sinta_rank"),
                is_scopus_indexed=j_data.get("is_scopus_indexed", False),
                scimago_quartile=scim_q,
                sjr_score=scim_sjr,
                scimago_url=scim_url,
                h_index=scim_h,
                scopus_coverage_start=j_data.get("scopus_coverage_start"),
                scopus_coverage_end=j_data.get("scopus_coverage_end"),
                sinta_id=j_data.get("sinta_id"),
                sinta_profile_url=j_data.get("sinta_profile_url"),
                scopus_source_url=j_data.get("scopus_source_url"),
                is_open_access=j_data.get("is_open_access", True),
                verification_source="curated_database",
                verified_at=datetime.now(timezone.utc),
            )
            db.add(journal)

    db.commit()
    logger.info("Curated journal synchronization completed.")


def seed_journals_if_empty(db: Session) -> None:
    """Seed reference journals into database if empty."""
    count = db.query(Journal).count()
    if count == 0:
        sync_curated_journals(db)


def find_or_verify_journal(
    db: Session,
    journal_name: Optional[str],
    issn: Optional[str] = None,
    eissn: Optional[str] = None,
) -> Optional[Journal]:
    """
    Find matching journal in DB or curated reference, or auto-detect indexing indicators.
    Authoritative curated database and SCImago (https://www.scimagojr.com/) take precedence.
    """
    if not journal_name and not issn and not eissn:
        return None

    clean_issn = (issn or "").replace("-", "").strip()
    clean_eissn = (eissn or "").replace("-", "").strip()
    norm_target = normalize_string(journal_name)

    # 1. Authoritative check in KNOWN_JOURNALS first
    ref_match = _match_known_journal(norm_target, issn, eissn)
    if ref_match:
        # Check if already present in DB
        existing = db.query(Journal).filter(Journal.name == ref_match["name"]).first()
        if not existing and clean_issn:
            existing = db.query(Journal).filter(
                (Journal.issn == clean_issn) | (Journal.eissn == clean_issn)
            ).first()

        sjr_data = verify_journal_scimago(ref_match["name"], issn, eissn)

        if existing:
            # Sync rank and Scopus status
            if existing.sinta_rank != ref_match.get("sinta_rank") or existing.is_scopus_indexed != ref_match.get("is_scopus_indexed"):
                existing.sinta_rank = ref_match.get("sinta_rank")
                existing.is_scopus_indexed = ref_match.get("is_scopus_indexed", False)
                if sjr_data:
                    existing.scimago_quartile = sjr_data.get("scimago_quartile")
                    existing.sjr_score = sjr_data.get("sjr_score")
                    existing.scimago_url = sjr_data.get("scimago_url")
                    existing.h_index = sjr_data.get("h_index")
                existing.verification_source = "curated_database"
                db.commit()
            return existing

        # Create new journal from curated entry
        new_journal = Journal(
            name=ref_match["name"],
            issn=ref_match.get("issn"),
            eissn=ref_match.get("eissn"),
            publisher=ref_match.get("publisher"),
            sinta_rank=ref_match.get("sinta_rank"),
            is_scopus_indexed=ref_match.get("is_scopus_indexed", False),
            scimago_quartile=sjr_data.get("scimago_quartile") if sjr_data else None,
            sjr_score=sjr_data.get("sjr_score") if sjr_data else None,
            scimago_url=sjr_data.get("scimago_url") if sjr_data else ref_match.get("scopus_source_url"),
            h_index=sjr_data.get("h_index") if sjr_data else None,
            scopus_coverage_start=ref_match.get("scopus_coverage_start"),
            scopus_coverage_end=ref_match.get("scopus_coverage_end"),
            sinta_id=ref_match.get("sinta_id"),
            sinta_profile_url=ref_match.get("sinta_profile_url"),
            scopus_source_url=ref_match.get("scopus_source_url"),
            is_open_access=ref_match.get("is_open_access", True),
            verification_source="curated_database",
            verified_at=datetime.now(timezone.utc),
        )
        db.add(new_journal)
        db.commit()
        db.refresh(new_journal)
        return new_journal

    # 2. ISSN Match in DB
    if clean_issn:
        j = db.query(Journal).filter(
            (Journal.issn == clean_issn) | (Journal.eissn == clean_issn)
        ).first()
        if j:
            return j

    if clean_eissn:
        j = db.query(Journal).filter(
            (Journal.issn == clean_eissn) | (Journal.eissn == clean_eissn)
        ).first()
        if j:
            return j

    if not norm_target:
        return None

    # 3. Match existing DB journals by name
    all_journals = db.query(Journal).all()
    for j in all_journals:
        norm_j = normalize_string(j.name)
        if norm_j == norm_target or (len(norm_target) > 7 and (norm_target in norm_j or norm_j in norm_target)):
            return j

    # 4. Authoritative SCImago Verification (https://www.scimagojr.com/)
    # Real-time verification against the SCImago Journal Rank database containing 30,000+ Scopus journals.
    scimago_res = verify_journal_scimago(journal_name, issn, eissn)
    if scimago_res:
        created = Journal(
            name=scimago_res.get("scimago_title") or journal_name,
            issn=issn,
            eissn=eissn,
            sinta_rank=None,
            is_scopus_indexed=True,
            scimago_quartile=scimago_res.get("scimago_quartile"),
            sjr_score=scimago_res.get("sjr_score"),
            scimago_url=scimago_res.get("scimago_url"),
            h_index=scimago_res.get("h_index"),
            verification_source="scimago_jr_database",
            verified_at=datetime.now(timezone.utc),
        )
        db.add(created)
        db.commit()
        db.refresh(created)
        return created

    # 5. Non-Scopus fallback: Journal is not indexed in Scopus / SCImago
    created = Journal(
        name=journal_name,
        issn=issn,
        eissn=eissn,
        sinta_rank=None,
        is_scopus_indexed=False,  # NOT in SCImago -> Not Scopus!
        scimago_quartile=None,
        sjr_score=None,
        scimago_url=f"https://www.scimagojr.com/journalsearch.php?q={norm_target.replace(' ', '%20')}",
        verification_source="unverified_non_scopus",
        verified_at=datetime.now(timezone.utc),
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return created


def verify_and_link_article(
    db: Session,
    article: Article,
    issn: Optional[str] = None,
    eissn: Optional[str] = None,
) -> Tuple[Optional[Journal], str]:
    """
    Verify journal indexing for an article, link to journal, and determine verification_status.
    Returns (journal, verification_status_string).
    """
    journal = None
    if article.journal_id:
        journal = db.query(Journal).filter(Journal.id == article.journal_id).first()

    if not journal and article.journal_name:
        journal = find_or_verify_journal(db, article.journal_name, issn, eissn)
        if journal:
            article.journal_id = journal.id

    # Determine status
    status = VerificationStatus.NOT_VERIFIED
    if journal:
        if journal.is_scopus_indexed and journal.sinta_rank:
            status = VerificationStatus.VERIFIED_BOTH
        elif journal.is_scopus_indexed:
            status = VerificationStatus.VERIFIED_SCOPUS
        elif journal.sinta_rank:
            status = VerificationStatus.VERIFIED_SINTA

    article.verification_status = status
    db.commit()
    return journal, status


def get_scopus_verification_links(journal_name: str, issn: Optional[str] = None) -> Dict[str, str]:
    """Generate direct verification links for Scopus Sources, SCImago (SJR), and SINTA."""
    clean_jname = journal_name.strip() if journal_name else ""
    encoded_jname = clean_jname.replace(" ", "%20")
    clean_issn = (issn or "").replace("-", "").strip()

    scimago_query = clean_issn if clean_issn else encoded_jname
    return {
        "scopus_sources": f"https://www.scopus.com/sources.uri?query={encoded_jname}",
        "scimago_sjr": f"https://www.scimagojr.com/journalsearch.php?q={scimago_query}&tip=iss",
        "elsevier_dev": "https://dev.elsevier.com/",
        "sinta_kemdikbud": f"https://sinta.kemdikbud.go.id/journals?q={encoded_jname}",
        "doaj_search": f"https://doaj.org/search/journals?source=%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22{encoded_jname}%22%7D%7D%7D",
        "unpaywall": f"https://unpaywall.org/search?q={encoded_jname}",
        "core": f"https://core.ac.uk/search?q={encoded_jname}",
    }
