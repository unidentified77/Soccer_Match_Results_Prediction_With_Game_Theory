#!/usr/bin/env python3
# simule.py  –  batch Final-Team-Power + skor arşivi
# --------------------------------------------------
from __future__ import annotations
import os, time, logging, requests, pandas as pd
from typing import Dict, List

#────────────────────────  AYARLAR  ────────────────────────#
API_KEY     = "078dfd2522b94892b4675b57bd810999"
LEAGUE_ID   = 39                               # Premier League
SEASONS     = ["2023", "2024"]                 # son iki sezon
OUT_FILE    = "season_team_powers.xlsx"        # çıktı
HIST_FILE   = "history_df.xlsx"                # formasyon-stil geçmişi
SKIP_FIRST  = 14                               # Excel’de hali-hazırda var

#────────────────────────  DIŞ MODÜLLER  ───────────────────#
from match_player_power_calculator import calculate_match_player_powers
from synergycheck   import synergy_from_formation_style
from team_power     import Team, fill_all_stats
from utils          import UnderstatClient                         # FBref throttle

#────────────────────────  LOGGING  ─────────────────────────#
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")

BASE_URL = "https://v3.football.api-sports.io"
HEADERS  = {"x-apisports-key": API_KEY, "accept": "application/json"}


# ╭────────────  yardımcı fonksiyonlar  ───────────╮
def fixtures_finished(season: str) -> List[Dict]:
    """Belirli sezonun FT durumundaki tüm maçları döndürür."""
    p = {"league": LEAGUE_ID, "season": season, "status": "FT"}
    r = requests.get(f"{BASE_URL}/fixtures", headers=HEADERS, params=p, timeout=20)
    r.raise_for_status()
    return r.json()["response"]


def synergy_bonus(hf: str, hs: str, af: str, as_: str) -> tuple[float, float]:
    try:
        hist = pd.read_excel(HIST_FILE)
    except Exception as e:
        logging.warning("synergy=0  (%s)", e)
        return 0.0, 0.0
    return synergy_from_formation_style(hf, hs, af, as_, hist)


def calc_final_power(fx_id: int, season: str) -> Dict | None:
    """Tek maç için power + skor hesaplar, dict döner; eksik veride None."""
    ppl = calculate_match_player_powers(str(fx_id), season, SEASONS)
    if not ppl:
        return None

    first = {s: sum(p["power"] for p in ppl[s]["first_eleven"]) for s in ppl}

    lu = requests.get(f"{BASE_URL}/fixtures/lineups",
                      headers=HEADERS,
                      params={"fixture": fx_id}, timeout=12).json().get("response", [])
    if len(lu) < 2:
        return None
    h_name, a_name = lu[0]["team"]["name"], lu[1]["team"]["name"]

    with UnderstatClient() as us:
        home, away = Team(h_name, h_name[:3]), Team(a_name, a_name[:3])
        fill_all_stats(home, season, str(int(season)-1), SEASONS, us)
        fill_all_stats(away, season, str(int(season)-1), SEASONS, us)

    hf, af = home.last_match_formation or "4-3-3", away.last_match_formation or "4-4-2"
    hs, as_ = home.style or "Attacking",            away.style or "Defensive"
    syn_h, syn_a = synergy_bonus(hf, hs, af, as_)
    ov_h,  ov_a  = home.calculate_team_strength(), away.calculate_team_strength()

    fx = requests.get(f"{BASE_URL}/fixtures",
                      headers=HEADERS,
                      params={"id": fx_id}).json()["response"][0]
    score_txt = f"{fx['goals']['home']}-{fx['goals']['away']}"

    return dict(
        fixture_id   = fx_id,
        Home_Team    = h_name,
        Away_Team    = a_name,
        Match_Score  = score_txt,
        Home_Power   = round(first['home'] + syn_h + ov_h, 2),
        Away_Power   = round(first['away'] + syn_a + ov_a, 2),
    )


def append_row_excel(df_existing: pd.DataFrame, row: Dict):
    cols = ["fixture_id","Home_Team","Away_Team",
            "Match_Score","Home_Power","Away_Power"]

    df_new = pd.concat([df_existing, pd.DataFrame([row], columns=cols)],
                       ignore_index=True)
    df_new.to_excel(OUT_FILE, index=False)
    logging.info("💾 eklendi  %s  (toplam satır=%d)",
                 row["fixture_id"], len(df_new))
    return df_new   # geri döndür, sonraki kontrol için


# ╰──────────────────────────────────────────────────╯

def main():
    # 0) Excel’i oku – varsa mevcut fixture_id set’ini al
    if os.path.exists(OUT_FILE):
        df = pd.read_excel(OUT_FILE)
        existing_ids = set(df.fixture_id)
        logging.info("🗂  mevcut dosya bulundu (%d satır)", len(df))
    else:
        df = pd.DataFrame()
        existing_ids = set()

    # 1) Mevcut dosyada ilk SKIP_FIRST satır varsa → onlar “skip list”
    skip_ids_manual = set(df.head(SKIP_FIRST).fixture_id) if len(df) >= SKIP_FIRST else set()

    for season in SEASONS:
        logging.info("=== SEASON %s ===", season)
        for fx in fixtures_finished(season):
            fid = fx["fixture"]["id"]

            # a) Dosyada zaten varsa
            if fid in existing_ids:
                logging.debug("⏩ atlanıyor (zaten var) %s", fid)
                continue
            # b) İlk 14 maç özel olarak atla
            if fid in skip_ids_manual:
                logging.debug("⏩ atlanıyor (first-14) %s", fid)
                continue

            try:
                res = calc_final_power(fid, season)
                if res:
                    df = append_row_excel(df, res)
                    existing_ids.add(fid)
                else:
                    logging.warning("⚠️  atlandı (eksik veri) %s", fid)
            except Exception as e:
                logging.error("❌ hata %s → %s", fid, e)
            time.sleep(1.0)        # API’yi boğma

    logging.info("🏁 BİTTİ → %s  (toplam=%d)", OUT_FILE, len(df))


if __name__ == "__main__":
    main()