import os
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "support-monitor-secret")
_db_url = os.getenv("DATABASE_URL", "")
if _db_url:
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///support.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 300}

db = SQLAlchemy()
db.init_app(app)


CATEGORY_KEYWORDS = {
    "R&D": ["r&d", "연구개발", "기술개발", "연구과제", "기술사업화", "기술혁신"],
    "사업화": ["사업화", "성장지원", "판로", "마케팅", "수출", "내수", "경영", "혁신바우처", "스케일업"],
    "투자연계": ["투자", "펀드", "금융", "융자", "보증", "대출", "자금"],
    "입주지원": ["입주", "공간", "센터", "보육", "오피스", "시설"],
    "IR피칭": ["ir", "피칭", "데모데이", "투자유치", "발표"],
    "경진대회": ["경진", "공모전", "대회", "어워드", "contest", "경연"],
    "교육멘토링": ["교육", "멘토", "컨설팅", "세미나", "아카데미", "워크숍", "특강", "강좌"],
    "인력지원": ["인력", "채용", "인턴", "고용", "일자리", "파견"],
}


def classify_category(title, org="", snippet=""):
    text = f"{title} {org} {snippet}".lower()
    matched = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                matched.append(cat)
                break
    return ",".join(matched) if matched else "기타"


class SupportProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_site = db.Column(db.String(100), nullable=False)
    source_url = db.Column(db.String(1000), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    organization = db.Column(db.String(200), default="")
    deadline = db.Column(db.String(100), default="")
    status = db.Column(db.String(50), default="")
    category = db.Column(db.String(200), default="")
    content_snippet = db.Column(db.Text, default="")
    first_seen = db.Column(db.DateTime, default=datetime.now)
    is_new = db.Column(db.Boolean, default=True)
    is_bookmarked = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    hash_key = db.Column(db.String(64), unique=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "source_site": self.source_site,
            "source_url": self.source_url, "title": self.title,
            "organization": self.organization, "deadline": self.deadline,
            "status": self.status, "category": self.category,
            "content_snippet": self.content_snippet,
            "first_seen": self.first_seen.isoformat() if self.first_seen else "",
            "is_new": self.is_new, "is_bookmarked": self.is_bookmarked,
            "is_read": self.is_read,
        }


class ScrapeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_site = db.Column(db.String(100), nullable=False)
    scraped_at = db.Column(db.DateTime, default=datetime.now)
    success = db.Column(db.Boolean, default=True)
    items_found = db.Column(db.Integer, default=0)
    new_items = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, default="")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/support/programs")
def get_programs():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    source_site = request.args.get("source_site", "")
    filter_type = request.args.get("filter", "")
    search = request.args.get("search", "")
    cat_filter = request.args.get("category", "")

    q = SupportProgram.query
    if source_site:
        q = q.filter_by(source_site=source_site)
    if filter_type == "unread":
        q = q.filter_by(is_read=False)
    elif filter_type == "bookmarked":
        q = q.filter_by(is_bookmarked=True)
    elif filter_type == "read":
        q = q.filter_by(is_read=True)
    if cat_filter:
        q = q.filter(SupportProgram.category.ilike(f"%{cat_filter}%"))
    if search:
        q = q.filter(SupportProgram.title.ilike(f"%{search}%"))

    q = q.order_by(SupportProgram.first_seen.desc())
    total = q.count()
    programs = q.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "programs": [p.to_dict() for p in programs],
        "total": total, "page": page, "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    })


@app.route("/api/support/programs/<int:pid>/read", methods=["POST"])
def toggle_read(pid):
    p = SupportProgram.query.get_or_404(pid)
    p.is_read = not p.is_read
    db.session.commit()
    return jsonify({"ok": True, "is_read": p.is_read})


@app.route("/api/support/programs/mark-all-read", methods=["POST"])
def mark_all_read():
    SupportProgram.query.filter_by(is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/support/programs/<int:pid>/bookmark", methods=["POST"])
def toggle_bookmark(pid):
    p = SupportProgram.query.get_or_404(pid)
    p.is_bookmarked = not p.is_bookmarked
    db.session.commit()
    return jsonify({"ok": True, "is_bookmarked": p.is_bookmarked})


@app.route("/api/support/stats")
def get_stats():
    total = SupportProgram.query.count()
    unread_count = SupportProgram.query.filter_by(is_read=False).count()
    bookmark_count = SupportProgram.query.filter_by(is_bookmarked=True).count()
    sites = db.session.query(
        SupportProgram.source_site, db.func.count(SupportProgram.id)
    ).group_by(SupportProgram.source_site).all()

    # Count categories
    all_cats = {}
    for p in SupportProgram.query.with_entities(SupportProgram.category).all():
        for c in (p.category or "").split(","):
            c = c.strip()
            if c:
                all_cats[c] = all_cats.get(c, 0) + 1

    return jsonify({
        "total": total, "unread_count": unread_count,
        "bookmark_count": bookmark_count,
        "by_site": {s: c for s, c in sites},
        "by_category": all_cats,
    })


@app.route("/api/support/logs")
def get_logs():
    logs = ScrapeLog.query.order_by(ScrapeLog.scraped_at.desc()).limit(30).all()
    return jsonify({"logs": [{
        "id": l.id, "source_site": l.source_site,
        "scraped_at": l.scraped_at.isoformat() if l.scraped_at else "",
        "success": l.success, "items_found": l.items_found,
        "new_items": l.new_items, "error_message": l.error_message,
    } for l in logs]})


scrape_status = {"running": False, "done_count": 0, "total_count": 14, "new_items": 0, "failed": 0}


@app.route("/api/scrape/run", methods=["POST"])
def trigger_scrape():
    if scrape_status["running"]:
        return jsonify({"ok": False, "message": "이미 수집 중입니다."})

    from scrapers import ALL_SCRAPERS

    scrape_status["running"] = True
    scrape_status["done_count"] = 0
    scrape_status["total_count"] = len(ALL_SCRAPERS)
    scrape_status["new_items"] = 0
    scrape_status["failed"] = 0

    def do_scrape():
        with app.app_context():
            for scraper_cls in ALL_SCRAPERS:
                scraper = scraper_cls()
                log = scraper.scrape()
                scrape_status["done_count"] += 1
                if log.success:
                    scrape_status["new_items"] += log.new_items
                else:
                    scrape_status["failed"] += 1
            scrape_status["running"] = False

    threading.Thread(target=do_scrape, daemon=True).start()
    return jsonify({"ok": True, "message": "수집을 시작합니다."})


@app.route("/api/scrape/status")
def scrape_progress():
    return jsonify(scrape_status)


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
