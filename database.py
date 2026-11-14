import sqlite3, hashlib, os
from datetime import date
DB = "spendmate.db"

def conn():
    c = sqlite3.connect(DB)
    c.execute("PRAGMA foreign_keys=ON")
    return c

def password_hash(password):
    if len(password) < 6: raise ValueError("Password must be at least 6 characters.")
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 160000)
    return salt.hex() + ":" + key.hex()

def check_password(password, saved):
    try:
        salt, key = saved.split(":")
        return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 160000).hex() == key
    except Exception: return False

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tx_date TEXT NOT NULL,
            kind TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            UNIQUE(user_id, category),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            target REAL NOT NULL,
            saved REAL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS savings_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            saved_date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(goal_id) REFERENCES goals(id)
        );
        """)
def register_user(name,email,password):
    if not name.strip() or "@" not in email: raise ValueError("Enter a valid name and email.")
    with conn() as c: c.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",(name.strip(),email.strip().lower(),password_hash(password)))

def authenticate(email,password):
    with conn() as c: row=c.execute("SELECT id,password FROM users WHERE email=?",(email.strip().lower(),)).fetchone()
    return (row[0],) if row and check_password(password,row[1]) else None

def add_transaction(uid,tx_date,kind,category,description,amount):
    date.fromisoformat(tx_date)
    if kind not in ("income","expense") or not category.strip() or amount <= 0: raise ValueError("Enter valid details and an amount above zero.")
    with conn() as c: c.execute("INSERT INTO transactions(user_id,tx_date,kind,category,description,amount) VALUES(?,?,?,?,?,?)",(uid,tx_date,kind,category.strip(),description.strip(),amount))

def list_transactions(uid):
    with conn() as c:
        return c.execute(
            """SELECT id, user_id, tx_date, kind, category,
                      description, amount
               FROM transactions
               WHERE user_id=?
               ORDER BY tx_date DESC, id DESC""",
            (uid,)
        ).fetchall()
def delete_transaction(txid,uid):
    with conn() as c: c.execute("DELETE FROM transactions WHERE id=? AND user_id=?",(txid,uid))

def get_dashboard(uid):
    with conn() as c:
        inc=c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND kind='income'",(uid,)).fetchone()[0]
        exp=c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND kind='expense'",(uid,)).fetchone()[0]
    return {"income":inc,"expense":exp,"balance":inc-exp}

def set_budget(uid,cat,amount):
    if not cat.strip() or amount<=0: raise ValueError("Enter a category and a positive budget.")
    with conn() as c: c.execute("INSERT INTO budgets(user_id,category,monthly_limit) VALUES(?,?,?) ON CONFLICT(user_id,category) DO UPDATE SET monthly_limit=excluded.monthly_limit",(uid,cat.strip(),amount))

def get_budgets(uid):
    with conn() as c:
        return c.execute("""SELECT b.category,b.monthly_limit,COALESCE((SELECT SUM(t.amount) FROM transactions t WHERE t.user_id=b.user_id AND t.kind='expense' AND t.category=b.category AND substr(t.tx_date,1,7)=strftime('%Y-%m','now')),0) FROM budgets b WHERE b.user_id=?""",(uid,)).fetchall()

def add_goal(uid,name,target):
    if not name.strip() or target<=0: raise ValueError("Enter a goal name and positive target.")
    with conn() as c: c.execute("INSERT INTO goals(user_id,name,target) VALUES(?,?,?)",(uid,name.strip(),target))

def add_savings(uid, goal_id, amount):
    if amount <= 0:
        raise ValueError("Enter a valid savings amount.")

    with conn() as c:
        goal = c.execute(
            "SELECT target, saved FROM goals WHERE id=? AND user_id=?",
            (goal_id, uid)
        ).fetchone()

        if goal is None:
            raise ValueError("Savings goal not found.")

        target, saved = goal

        if saved + amount > target:
            raise ValueError(
                f"You can add only Rs.{target - saved:.2f} more."
            )

        today = date.today().isoformat()

        c.execute(
            "UPDATE goals SET saved = saved + ? WHERE id=? AND user_id=?",
            (amount, goal_id, uid)
        )

        c.execute(
            """INSERT INTO savings_history
            (user_id, goal_id, amount, saved_date)
            VALUES (?, ?, ?, ?)""",
            (uid, goal_id, amount, today)
        )
def get_goals(uid):
    with conn() as c:
        return c.execute(
            """SELECT id, name, target, saved
            FROM goals
            WHERE user_id=?""",
            (uid,)
        ).fetchall()
        
def get_savings_history(uid, goal_id):
    with conn() as c:
        return c.execute(
            """SELECT amount, saved_date
            FROM savings_history
            WHERE user_id=? AND goal_id=?
            ORDER BY saved_date DESC, id DESC""",
            (uid, goal_id)
        ).fetchall()