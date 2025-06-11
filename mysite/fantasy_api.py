# fantasy_api.py  –– Auth + fantasy-bet endpoints (ported from api5.php)
from __future__ import annotations
import functools, secrets, time, datetime as dt
import requests, pymysql, werkzeug.security as wz
from flask import Blueprint, request, jsonify, g, current_app as app

bp = Blueprint("fantasy", __name__)

# -----------------------------------------------------------
#  Helpers
# -----------------------------------------------------------
def _db():
    """Reuse the connection factory that already exists in flask_app.py.
       Here we import it dynamically to avoid circular import."""
    from flask_app import _db as _core_db  # type: ignore
    return _core_db()

def token_hex(n=40):       # 40‒byte token like PHP version
    return secrets.token_hex(n // 2)

def json_ok(data, code=200):
    return jsonify(data), code

def json_err(msg, code=400):
    return jsonify({"error": msg}), code

def require_json(fields: list[str]):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            data = request.get_json(silent=True) or {}
            missing = [f for f in fields if not data.get(f)]
            if missing:
                return json_err(f"missing: {', '.join(missing)}", 400)
            g.json = data
            return fn(*a, **kw)
        return wrapper
    return deco

def auth_required(fn):
    """decorator that loads g.user (row) if token valid"""
    @functools.wraps(fn)
    def wrapper(*a, **kw):
        token = request.headers.get("Authorization") or ""
        if not token:
            return json_err("No token", 401)
        with _db().cursor() as cur:
            cur.execute("SELECT id,name FROM fp_users WHERE token=%s LIMIT 1", (token,))
            user = cur.fetchone()
        if not user:
            return json_err("Invalid token", 401)
        g.user = user
        return fn(*a, **kw)
    return wrapper

# -----------------------------------------------------------
# 1.  SIGN-UP
# -----------------------------------------------------------
@bp.route("/signup", methods=["POST"])
@require_json(["name", "email", "password"])
def signup():
    j = g.json
    name, email, pwd = j["name"].strip(), j["email"].strip(), j["password"]
    if len(pwd) < 6:
        return json_err("Password too short", 400)

    with _db().cursor() as cur:
        cur.execute("SELECT id FROM fp_users WHERE email=%s LIMIT 1", (email,))
        if cur.fetchone():
            return json_err("E-mail already in use", 409)

        token = token_hex()
        cur.execute(
            """INSERT INTO fp_users (name,email,password,token)
               VALUES (%s,%s,%s,%s)""",
            (name, email, wz.generate_password_hash(pwd), token))
    return json_ok({"success": True, "token": token, "name": name})

# -----------------------------------------------------------
# 2.  LOGIN (email/password)
# -----------------------------------------------------------
@bp.route("/login", methods=["POST"])
@require_json(["email", "password"])
def login():
    j = g.json; email, pwd = j["email"], j["password"]
    with _db().cursor() as cur:
        cur.execute("""SELECT id,name,password FROM fp_users
                       WHERE email=%s LIMIT 1""", (email,))
        row = cur.fetchone()
    if not row or not wz.check_password_hash(row["password"], pwd):
        return json_err("Wrong e-mail / password", 401)

    token = token_hex()
    with _db().cursor() as cur:
        cur.execute("UPDATE fp_users SET token=%s WHERE id=%s", (token, row["id"]))
    return json_ok({"success": True, "token": token, "name": row["name"]})

# -----------------------------------------------------------
# 3.  LOGIN  (Google One-Tap)
# -----------------------------------------------------------
@bp.route("/loginSocial", methods=["POST"])
@require_json(["provider", "token", "name", "email"])
def login_social():
    j = g.json
    if j["provider"] != "google":
        return json_err("Unsupported provider", 400)

    verify = requests.get(
        "https://oauth2.googleapis.com/tokeninfo",
        params={"id_token": j["token"]}, timeout=8).json()
    if "email" not in verify or "sub" not in verify:
        return json_err("Invalid Google token", 401)

    sub, email, name = verify["sub"], verify["email"], j["name"]
    token = token_hex()

    with _db().cursor() as cur:
        cur.execute("""SELECT id,name FROM fp_users
                       WHERE provider='google' AND social_sub=%s LIMIT 1""", (sub,))
        user = cur.fetchone()

        if user:                               # -- existing google user
            uid = user["id"]
            cur.execute("UPDATE fp_users SET token=%s WHERE id=%s", (token, uid))

        else:                                  # -- insert or link
            cur.execute("SELECT id FROM fp_users WHERE email=%s LIMIT 1", (email,))
            row = cur.fetchone()
            if row:                            # link local → google
                uid = row["id"]
                cur.execute("""UPDATE fp_users
                               SET provider='google',social_sub=%s,token=%s
                               WHERE id=%s""", (sub, token, uid))
            else:                              # create new
                cur.execute("""INSERT INTO fp_users
                               (name,email,password,provider,social_sub,token)
                               VALUES (%s,%s,NULL,'google',%s,%s)""",
                            (name, email, sub, token))
                uid = cur.lastrowid
    return json_ok({"success": True, "token": token, "name": name})

# -----------------------------------------------------------
# 4.  FANTASY PROFILE
# -----------------------------------------------------------
@bp.route("/fantasy/profile")
@auth_required
def fantasy_profile():
    uid = g.user["id"]
    with _db().cursor() as cur:
        cur.execute("SELECT * FROM fp_fantasy_profiles WHERE user_id=%s LIMIT 1", (uid,))
        profile = cur.fetchone()
        if not profile:
            cur.execute("""INSERT INTO fp_fantasy_profiles
                           (user_id,balance,total_bets,won_bets)
                           VALUES (%s,1000,0,0)""", (uid,))
            profile = {
                "user_id": uid, "balance": 1000, "total_bets": 0,
                "won_bets": 0, "total_winnings": 0, "weekly_rank": None,
                "season_rank": None
            }

        cur.execute("""SELECT badge_type,earned_at
                       FROM fp_user_badges WHERE user_id=%s
                       ORDER BY earned_at DESC""", (uid,))
        badges = cur.fetchall()
    profile["name"] = g.user["name"]
    profile["badges"] = badges
    return json_ok(profile)

# -----------------------------------------------------------
# 5.  PLACE FANTASY BET
# -----------------------------------------------------------
@bp.route("/fantasy/bet", methods=["POST"])
@auth_required
@require_json(["fixture_id", "bet_type", "amount", "odd"])
def place_bet():
    j = g.json; uid = g.user["id"]
    fixture_id, bet_type = int(j["fixture_id"]), j["bet_type"]
    amount, odd = int(j["amount"]), float(j["odd"])

    if bet_type not in ("home", "draw", "away") or not 10 <= amount <= 500:
        return json_err("Invalid bet data", 400)

    with _db().cursor() as cur:
        # balance check
        cur.execute("SELECT balance FROM fp_fantasy_profiles WHERE user_id=%s", (uid,))
        bal = cur.fetchone()["balance"]
        if bal < amount:
            return json_err("Insufficient balance", 400)

        # duplicate check
        cur.execute("""SELECT id FROM fp_fantasy_bets
                       WHERE user_id=%s AND fixture_id=%s LIMIT 1""",
                    (uid, fixture_id))
        if cur.fetchone():
            return json_err("Already bet on this match", 400)

        cur.execute("""INSERT INTO fp_fantasy_bets
                       (user_id,fixture_id,bet_type,amount,odd,placed_at)
                       VALUES (%s,%s,%s,%s,%s,NOW())""",
                    (uid, fixture_id, bet_type, amount, odd))
        cur.execute("""UPDATE fp_fantasy_profiles
                       SET balance = balance - %s WHERE user_id=%s""",
                    (amount, uid))
    return json_ok({"success": True, "new_balance": bal - amount})

# -----------------------------------------------------------
# 6.  LIST /bets
# -----------------------------------------------------------
@bp.route("/fantasy/bets")
@auth_required
def list_bets():
    status = request.args.get("status", "active")  # active|completed|all
    uid = g.user["id"]

    where = ["user_id=%s"]
    if status == "active":
        where.append("result IS NULL")
    elif status == "completed":
        where.append("result IS NOT NULL")

    with _db().cursor() as cur:
        cur.execute(f"""SELECT * FROM fp_fantasy_bets
                        WHERE {' AND '.join(where)}
                        ORDER BY placed_at DESC LIMIT 50""", (uid,))
        bets = cur.fetchall()
    return json_ok({"bets": bets})

# -----------------------------------------------------------
# 7.  LEADERBOARD
# -----------------------------------------------------------
@bp.route("/fantasy/leaderboard")
def leaderboard():
    period = request.args.get("period", "weekly")  # weekly|monthly|season
    limit  = min(int(request.args.get("limit", 20)), 100)

    date_sql = ""
    if period == "weekly":
        date_sql = "AND b.placed_at >= DATE_SUB(NOW(),INTERVAL 7 DAY)"
    elif period == "monthly":
        date_sql = "AND b.placed_at >= DATE_SUB(NOW(),INTERVAL 30 DAY)"

    sql = f"""
      SELECT u.id user_id,u.name,
             COUNT(b.id) total_bets,
             SUM(b.result='won') won_bets,
             COALESCE(SUM(CASE WHEN b.result='won' THEN b.amount*b.odd END),0) -
             COALESCE(SUM(b.amount),0) profit,
             ROUND(SUM(b.result='won')*100/COUNT(b.id),1) win_rate
      FROM fp_users u
      JOIN fp_fantasy_profiles p ON p.user_id=u.id
      LEFT JOIN fp_fantasy_bets b ON b.user_id=u.id {date_sql}
      GROUP BY u.id
      HAVING total_bets>0
      ORDER BY profit DESC
      LIMIT %s
    """
    with _db().cursor() as cur:
        cur.execute(sql, (limit,))
        rows = cur.fetchall()
        for i, r in enumerate(rows, start=1):
            r["rank"] = i
    return json_ok({"leaderboard": rows, "period": period})

# -----------------------------------------------------------
# 8.  PROCESS RESULTS  (Cron use)
# -----------------------------------------------------------
@bp.route("/fantasy/processResults", methods=["POST"])
def process_results():
    """Intended for cron or admin use – no auth to keep example short;
       protect with secret header in production."""
    processed = 0
    with _db().cursor() as cur:
        cur.execute("""SELECT b.id,b.user_id,b.fixture_id,b.bet_type,b.amount,b.odd
                       FROM fp_fantasy_bets b
                       WHERE b.result IS NULL
                         AND b.fixture_id IN
                           (SELECT id FROM fixtures_cache WHERE status='FT')""")
        bets = cur.fetchall()

    for bet in bets:
        with _db().cursor() as cur:
            cur.execute("""SELECT goalsHome,goalsAway
                           FROM fixtures_cache WHERE id=%s""",
                        (bet["fixture_id"],))
            fx = cur.fetchone()
        if not fx:
            continue

        # decide outcome
        outcome = ("home" if fx["goalsHome"] > fx["goalsAway"]
                   else "away" if fx["goalsAway"] > fx["goalsHome"] else "draw")
        won = (outcome == bet["bet_type"])
        result, win_amt = ("won", bet["amount"] * bet["odd"]) if won else ("lost", 0)

        with _db().cursor() as cur:
            cur.execute("""UPDATE fp_fantasy_bets
                           SET result=%s,winnings=%s WHERE id=%s""",
                        (result, win_amt, bet["id"]))
            cur.execute("""UPDATE fp_fantasy_profiles
                           SET total_bets = total_bets+1,
                               balance = balance+%s,
                               won_bets = won_bets+%s,
                               total_winnings = total_winnings+%s
                           WHERE user_id=%s""",
                        (win_amt, int(won), win_amt, bet["user_id"]))
        processed += 1
        check_badges(bet["user_id"])
    return json_ok({"success": True, "processed": processed})

# -----------------------------------------------------------
#  Badge helper
# -----------------------------------------------------------
def check_badges(uid: int):
    with _db().cursor() as cur:
        cur.execute("""SELECT total_bets,won_bets,total_winnings
                       FROM fp_fantasy_profiles WHERE user_id=%s""", (uid,))
        st = cur.fetchone()

    targets = []
    if st["won_bets"] >= 1:  targets.append("first_win")
    if st["won_bets"] >= 5:  targets.append("streak_5")
    if st["total_winnings"] >= 5000: targets.append("high_roller")
    if st["total_bets"] >= 100:      targets.append("veteran")

    if not targets:
        return
    with _db().cursor() as cur:
        cur.executemany("""INSERT IGNORE INTO fp_user_badges
                           (user_id,badge_type,earned_at)
                           VALUES (%s,%s,NOW())""",
                        [(uid,t) for t in targets])