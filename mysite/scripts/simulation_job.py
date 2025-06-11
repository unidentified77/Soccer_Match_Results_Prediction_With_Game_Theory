# ~/mysite/scripts/simulation_job.py
# -----------------------------------------------------------
import datetime as dt, pymysql, logging, os, sys, pathlib, random
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tactics import determine_team_play_style
from utils import UnderstatClient                       # throttled versiyon
from team_power import Team, fill_all_stats
from simulation import simulate_100_matches             # senin dosyan
from final_team_power_calculator import calculate_final_team_powers

# ------------ DB helper --------------------------------------------------
def _db():
    conn = pymysql.connect(
        host      = os.getenv('DB_HOST', 'volkanerene.mysql.pythonanywhere-services.com'),
        user      = os.getenv('DB_USER'),
        password  = os.getenv('DB_PASS'),
        database  = os.getenv('DB_NAME'),
        autocommit=True,
        charset   ='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )
    conn.ping(reconnect=True)
    return conn



def save_sim(row: dict):
    with _db().cursor() as c:
        c.execute("""REPLACE INTO pl_fixture_sim
                     (fixture_id,sim_home_goals,sim_away_goals,sim_runs,calc_ts)
                     VALUES (%s,%s,%s,100,%s)""",
                  (row['fixture_id'], row['sim_home_goals'],
                   row['sim_away_goals'], dt.datetime.utcnow()))

# ------------ public entry ----------------------------------------------
def run_simulation_for_fixture(fxid: int,
                               home_power: float,
                               away_power: float) -> None:
    # takımların stilini Understat + kendi fonksiyonlarınla çek
    with UnderstatClient() as us:
        # çok hafif → sadece stil ve formasyon lazım
        # team isimlerini power fonk.’tan tekrar alalım
        pow_res = calculate_final_team_powers(str(fxid))
        ht_name, at_name = pow_res['home_team'], pow_res['away_team']

        home = Team(ht_name, ht_name[:3].upper())
        away = Team(at_name, at_name[:3].upper())

        fill_all_stats(home,  "2024", "2023", ["2023","2024"], us)
        fill_all_stats(away,  "2024", "2023", ["2023","2024"], us)

        style_h = determine_team_play_style(home)
        style_a = determine_team_play_style(away)

    # 100 kez maç simülasyonu
    avg_h, avg_a = simulate_100_matches(style_h, style_a,
                                        home_power, away_power)

    save_sim(dict(fixture_id=fxid,
                  sim_home_goals=round(avg_h,2),
                  sim_away_goals=round(avg_a,2)))
    logging.info("🔮 sim done %s  %.2f-%.2f", fxid, avg_h, avg_a)