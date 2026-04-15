from scrapers.sites.k_startup import KStartupScraper
from scrapers.sites.bizinfo import BizinfoScraper
from scrapers.sites.bsia import BsiaScraper
from scrapers.sites.busan_startup import BusanStartupScraper
from scrapers.sites.mss import MssScraper
from scrapers.sites.kidp import KidpScraper
from scrapers.sites.dcb import DcbScraper
from scrapers.sites.arte import ArteScraper
from scrapers.sites.kocca import KoccaScraper
from scrapers.sites.btp import BtpScraper
from scrapers.sites.bepa import BepaScraper, BkicScraper
from scrapers.sites.ssobiz import SsobizScraper
from scrapers.sites.smtech import SmtechScraper

ALL_SCRAPERS = [
    KStartupScraper, BizinfoScraper, BsiaScraper, BusanStartupScraper,
    MssScraper, KidpScraper, DcbScraper, ArteScraper, KoccaScraper,
    BtpScraper, BepaScraper, BkicScraper, SsobizScraper, SmtechScraper,
]


def run_all_scrapers():
    from app import SupportProgram
    from datetime import datetime

    print(f"\n{'='*50}")
    print(f"스크래핑 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    all_logs = []
    for scraper_cls in ALL_SCRAPERS:
        scraper = scraper_cls()
        log = scraper.scrape()
        all_logs.append(log)

    total_new = sum(l.new_items for l in all_logs if l.success)
    total_found = sum(l.items_found for l in all_logs if l.success)
    failed = sum(1 for l in all_logs if not l.success)

    print(f"\n{'='*50}")
    print(f"스크래핑 완료: 총 {total_found}건 발견, {total_new}건 신규, {failed}건 실패")
    print(f"{'='*50}\n")

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    new_programs = SupportProgram.query.filter(
        SupportProgram.first_seen >= today,
        SupportProgram.is_new == True
    ).all()

    return [p.to_dict() for p in new_programs]
