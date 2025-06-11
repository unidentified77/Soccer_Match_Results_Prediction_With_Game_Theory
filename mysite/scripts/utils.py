"""
utils.py  ─  Ortak yardımcılar + FBref yavaşlatma
=================================================

•   Tüm  `sd.FBref(…)` çağrılarını **otomatik** olarak
    –   tek bir `requests.Session`
    –   5 denemeye kadar “retry + exponential back-off”
    –   minimum 1.2 sn aralıklı istek

•   Gerektiğinde `get_fbref()` yardımcı fonksiyonunu
    kullanarak aynı FBref nesnesini yeniden kullanabilirsiniz.
"""

from __future__ import annotations
import warnings, logging, os, pathlib, requests
from requests.adapters import HTTPAdapter, Retry

# ───────────────────────── 1. Gürültüyü kapat  ──────────────────────
warnings.filterwarnings("ignore", category=FutureWarning)
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("soccerdata").setLevel(logging.CRITICAL)
logging.disable(logging.INFO)

# ───────────────────────── 2. Ortak dış kütüphaneler ───────────────
import pandas as pd
import numpy as np
import soccerdata as sd
from understatapi import UnderstatClient          # değişmedi

# ───────────────────────── 3. FBref throttle patch ──────────────────
#   (her yerde otomatik geçerli olacak)

# 3-a) İndirilen sayfaları diske ön-belleğe alalım  (~/.cache/soccerdata)
os.environ.setdefault(
    "SOCCERDATA_DIR",
    str(pathlib.Path.home() / ".cache" / "soccerdata")
)

def _slow_session() -> requests.Session:
    """Tek Session + otomatik retry/back-off ayarları."""
    sess = requests.Session()
    retry = Retry(
        total            = 5,                    # en çok 5 deneme
        backoff_factor   = 1.25,                 # 1.25 s → 2.5 s → 3.75 s …
        status_forcelist = (403, 429, 500, 502, 503, 504),
        raise_on_status  = False,
    )
    sess.mount("https://", HTTPAdapter(max_retries=retry))
    return sess

# 3-b) Orijinal ctor’u saklayıp sarmalayıcı oluştur
_FBref_orig = sd.FBref

def _FBref_patched(*args, **kw):
    """
    • `sleep_time` varsayılanı 1.2 sn  
    • Tüm isteklerde ortak Session (retry’li)
    """
    kw.setdefault("sleep_time", 1.2)
    kw.setdefault("session", _slow_session())
    return _FBref_orig(*args, **kw)

sd.FBref = _FBref_patched      # 🔥 monkey-patch

# 3-c) (opsiyonel) Aynı objeyi paylaşan yardımcı
_fbref_cache: dict[tuple[str, ...], sd.FBref] = {}

def get_fbref(seasons: tuple[str, ...] = ("2024-2025",)) -> sd.FBref:
    """
    Tek satırda paylaşımlı FBref:
        fb = get_fbref((season,))
    """
    key = tuple(seasons)
    if key not in _fbref_cache:
        _fbref_cache[key] = sd.FBref(
            leagues = "ENG-Premier League",
            seasons = list(seasons),
            sleep_time = 1.2,
            session = _slow_session(),
        )
    return _fbref_cache[key]

# ───────────────────────── 4. Dışa aktarılanlar ─────────────────────
__all__ = [
    "pd", "np",
    "sd",                 # patched FBref
    "get_fbref",
    "UnderstatClient",
]