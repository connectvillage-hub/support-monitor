import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from collections import defaultdict


def send_daily_digest(new_programs):
    sender = os.getenv("GMAIL_ADDRESS", "")
    app_password = os.getenv("GMAIL_APP_PASSWORD", "")
    recipient = os.getenv("NOTIFY_EMAIL", sender)

    if not sender or not app_password:
        print("Gmail 설정이 없어 이메일 발송을 건너뜁니다.")
        return False

    if not new_programs:
        return False

    today = datetime.now().strftime("%m/%d")
    subject = f"[지원사업 알림] 새로운 프로그램 {len(new_programs)}건 ({today})"

    html = build_digest_html(new_programs)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.sendmail(sender, recipient, msg.as_string())
        print(f"이메일 발송 완료: {recipient} ({len(new_programs)}건)")
        return True
    except Exception as e:
        print(f"이메일 발송 실패: {e}")
        return False


def build_digest_html(programs):
    by_site = defaultdict(list)
    for p in programs:
        site = p.get("source_site", "기타") if isinstance(p, dict) else p.source_site
        by_site[site].append(p)

    rows_html = ""
    for site, items in sorted(by_site.items()):
        rows_html += f'<tr><td colspan="3" style="background:#f0f4f8;padding:10px 12px;font-weight:700;font-size:14px;color:#1565C0;border-bottom:1px solid #ddd;">{site} ({len(items)}건)</td></tr>'
        for p in items:
            title = p.get("title", "") if isinstance(p, dict) else p.title
            url = p.get("source_url", "#") if isinstance(p, dict) else p.source_url
            org = p.get("organization", "") if isinstance(p, dict) else p.organization
            deadline = p.get("deadline", "") if isinstance(p, dict) else p.deadline
            rows_html += f'<tr><td style="padding:8px 12px;border-bottom:1px solid #eee;"><a href="{url}" style="color:#1976D2;text-decoration:none;font-size:13px;">{title}</a></td><td style="padding:8px 12px;border-bottom:1px solid #eee;color:#666;font-size:12px;">{org}</td><td style="padding:8px 12px;border-bottom:1px solid #eee;color:#666;font-size:12px;">{deadline}</td></tr>'

    return f'''<html><body style="font-family:-apple-system,'Malgun Gothic',sans-serif;background:#f5f5f5;padding:20px;">
    <div style="max-width:700px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <div style="background:#1565C0;color:#fff;padding:20px 24px;">
            <h1 style="margin:0;font-size:18px;">지원사업 알림</h1>
            <p style="margin:6px 0 0;font-size:13px;opacity:0.9;">{datetime.now().strftime("%Y년 %m월 %d일")} | 새로운 프로그램 {len(programs)}건</p>
        </div>
        <table style="width:100%;border-collapse:collapse;">
            <thead><tr style="background:#fafafa;">
                <th style="padding:10px 12px;text-align:left;font-size:12px;color:#888;border-bottom:2px solid #ddd;">제목</th>
                <th style="padding:10px 12px;text-align:left;font-size:12px;color:#888;border-bottom:2px solid #ddd;">주관기관</th>
                <th style="padding:10px 12px;text-align:left;font-size:12px;color:#888;border-bottom:2px solid #ddd;">마감일</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div></body></html>'''
