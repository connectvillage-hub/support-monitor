import hashlib
import re
import time
import traceback
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from scrapers.config import HEADERS, SCRAPE_DELAY


def is_current_period(title, deadline="", snippet=""):
    """과거 연도 공고 제외 + 마감일 지난 공고 제외."""
    now = datetime.now()
    cur_year = now.year
    text = f"{title} {deadline} {snippet}"

    # 제목에 과거 연도(2020~작년)가 명시되어 있고, 올해가 없으면 제외
    for y in range(2020, cur_year):
        if re.search(rf"{y}[년\s.\-]", text) and not re.search(rf"{cur_year}[년\s.\-]", text):
            return False

    # 마감일이 이미 지난 공고 제외
    if deadline:
        # 다양한 날짜 포맷에서 마감일 추출: 2026-04-10, 2026.04.10, 2026. 04. 10 등
        # "~" 이후 날짜가 실제 마감일
        dl_text = deadline.split("~")[-1].strip() if "~" in deadline else deadline.strip()
        m = re.search(r"(\d{4})\s*[\.\-/]\s*(\d{1,2})\s*[\.\-/]\s*(\d{1,2})", dl_text)
        if m:
            try:
                dl_date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 23, 59)
                if dl_date < now:
                    return False
            except ValueError:
                pass

    return True


class BaseScraper:
    site_name = ""
    list_url = ""
    verify_ssl = True

    def fetch_html(self, url=None):
        url = url or self.list_url
        resp = requests.get(url, headers=HEADERS, timeout=30, verify=self.verify_ssl)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text

    def fetch_json(self, url=None):
        url = url or self.list_url
        resp = requests.get(url, headers=HEADERS, timeout=30, verify=self.verify_ssl)
        resp.raise_for_status()
        return resp.json()

    def parse_programs(self, data):
        raise NotImplementedError

    def compute_hash(self, source_url):
        raw = f"{self.site_name}|{source_url}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def scrape(self):
        from app import db, SupportProgram, ScrapeLog, classify_category

        log = ScrapeLog(source_site=self.site_name, scraped_at=datetime.now())
        try:
            data = self.fetch_html() if not hasattr(self, "use_api") else self.fetch_json()
            programs = self.parse_programs(data)
            log.items_found = len(programs)

            new_count = 0
            for p in programs:
                # 과거 연도 공고 필터링
                if not is_current_period(p.get("title",""), p.get("deadline",""), p.get("content_snippet","")):
                    continue

                h = self.compute_hash(p["source_url"])
                if not SupportProgram.query.filter_by(hash_key=h).first():
                    cat = classify_category(p.get("title",""), p.get("organization",""), p.get("content_snippet",""))
                    db.session.add(SupportProgram(
                        source_site=self.site_name, source_url=p["source_url"],
                        title=p.get("title",""), organization=p.get("organization",""),
                        deadline=p.get("deadline",""), status=p.get("status",""),
                        category=cat, content_snippet=p.get("content_snippet",""),
                        first_seen=datetime.now(), is_new=True, is_read=False, hash_key=h,
                    ))
                    new_count += 1

            db.session.commit()
            log.new_items = new_count
            log.success = True
            print(f"  [{self.site_name}] {log.items_found}건 발견, {new_count}건 신규")
        except Exception as e:
            log.success = False
            log.error_message = traceback.format_exc()
            print(f"  [{self.site_name}] 오류: {e}")
            db.session.rollback()

        try:
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        time.sleep(SCRAPE_DELAY)
        return log
