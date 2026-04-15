"""
지원사업 스크래핑 실행 스크립트.
사용법: python scrapers/run.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from scrapers import run_all_scrapers
from scrapers.email_notify import send_daily_digest

if __name__ == "__main__":
    with app.app_context():
        new_programs = run_all_scrapers()
        if new_programs:
            send_daily_digest(new_programs)
        else:
            print("새로운 지원사업이 없습니다.")
