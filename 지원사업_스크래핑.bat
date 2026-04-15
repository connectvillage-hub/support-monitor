@echo off
cd /d "%~dp0"
python scrapers/run.py >> scraper_log.txt 2>&1
