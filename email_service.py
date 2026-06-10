import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings

logger = logging.getLogger(__name__)


def _send_blocking(to_email: str, subject: str, html_body: str) -> bool:
    
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP not configured — skipping email to %s (subject: %s)", to_email, subject)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, to_email, msg.as_string())
        logger.info("Email sent to %s — %s", to_email, subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False


async def _send(to_email: str, subject: str, html_body: str) -> bool:
    return await asyncio.to_thread(_send_blocking, to_email, subject, html_body)


async def send_alert_email(recipient_email: str, recipient_name: str) -> bool:
    subject = "🔔 Safety Check — Please Confirm Your Status"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#1e3a8a,#2563eb);padding:28px 32px;text-align:center;">
        <div style="font-size:2.5rem;">🚨</div>
        <h1 style="color:#fff;margin:12px 0 4px;font-size:1.4rem;">ResQmap</h1>
        <p style="color:rgba(255,255,255,.8);margin:0;font-size:.9rem;">Emergency Coordination System</p>
      </div>
      <div style="padding:32px;">
        <h2 style="color:#0f172a;margin:0 0 12px;">Safety Check Alert</h2>
        <p style="color:#334155;">Hi <strong>{recipient_name}</strong>,</p>
        <p style="color:#334155;">Emergency responders have sent you a <strong>safety check</strong>. Please log in to ResQmap and confirm your current status immediately.</p>
        <div style="background:#eff6ff;border:1px solid #93c5fd;border-radius:8px;padding:18px;margin:24px 0;">
          <p style="margin:0;color:#1e40af;font-weight:600;">What to do:</p>
          <ul style="color:#1e40af;margin:8px 0 0;padding-left:20px;">
            <li>Open the ResQmap app</li>
            <li>Respond to the safety check notification</li>
            <li>Tap <strong>✅ I'm Safe</strong> or <strong>🆘 I Need Help</strong></li>
          </ul>
        </div>
        <p style="color:#64748b;font-size:.875rem;">If you do not respond, your status will remain <strong>Unknown</strong> and rescue teams may be dispatched to your last known location.</p>
      </div>
      <div style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:16px 32px;text-align:center;">
        <p style="margin:0;color:#94a3b8;font-size:.78rem;">ResQmap Emergency Coordination · Do not reply to this email</p>
      </div>
    </div>
    """
    return await _send(recipient_email, subject, html)


async def send_rescue_email(recipient_email: str, recipient_name: str, coords: str = "Unknown") -> bool:
    subject = "🚨 Rescue Dispatch — Emergency Services Are On Their Way"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;background:#fff;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#7f1d1d,#dc2626);padding:28px 32px;text-align:center;">
        <div style="font-size:2.5rem;">🚑</div>
        <h1 style="color:#fff;margin:12px 0 4px;font-size:1.4rem;">ResQmap</h1>
        <p style="color:rgba(255,255,255,.8);margin:0;font-size:.9rem;">Emergency Coordination System</p>
      </div>
      <div style="padding:32px;">
        <h2 style="color:#dc2626;margin:0 0 12px;">🚨 Rescue Dispatch Confirmed</h2>
        <p style="color:#334155;">Hi <strong>{recipient_name}</strong>,</p>
        <p style="color:#334155;">Your status has been marked as <strong style="color:#dc2626;">DANGER</strong>. Emergency services have been dispatched to your location.</p>
        <div style="background:#fee2e2;border:1px solid #fca5a5;border-radius:8px;padding:18px;margin:24px 0;">
          <p style="margin:0 0 8px;color:#991b1b;font-weight:700;">📍 Coordinates on record:</p>
          <p style="margin:0;color:#991b1b;font-family:monospace;font-size:1rem;">{coords}</p>
        </div>
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:16px;margin-bottom:24px;">
          <p style="margin:0;color:#166534;font-weight:600;">While you wait for rescue:</p>
          <ul style="color:#166534;margin:8px 0 0;padding-left:20px;">
            <li>Stay in place if it is safe to do so</li>
            <li>Signal rescuers if possible (light, sound)</li>
            <li>Keep your device charged and location enabled</li>
            <li>Call <strong>911</strong> directly if you can</li>
          </ul>
        </div>
        <p style="color:#64748b;font-size:.875rem;">Rescue teams can see your real-time location on the dispatch map. Help is on the way.</p>
      </div>
      <div style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:16px 32px;text-align:center;">
        <p style="margin:0;color:#94a3b8;font-size:.78rem;">ResQmap Emergency Coordination · Do not reply to this email</p>
      </div>
    </div>
    """
    return await _send(recipient_email, subject, html)
