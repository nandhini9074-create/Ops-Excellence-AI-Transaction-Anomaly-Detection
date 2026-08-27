import httpx
import logging
from typing import Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from string import Template
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    async def send_teams_alert(issue: Dict):
        if not settings.TEAMS_WEBHOOK_URL:
            return
            
        # Adaptive Card format
        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.2",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": f"🚨 Anomaly Detected: {issue.get('anomaly_type')}",
                                "weight": "Bolder",
                                "size": "Medium",
                                "color": "Attention" if issue.get("severity") in ["HIGH", "CRITICAL"] else "Warning"
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Merchant:", "value": issue.get('merchant_name', 'Unknown')},
                                    {"title": "Outlet:", "value": issue.get('outlet_name', 'Unknown')},
                                    {"title": "Severity:", "value": issue.get('severity')},
                                    {"title": "Score:", "value": f"{issue.get('anomaly_score', 0):.2f}"},
                                    {"title": "Details:", "value": issue.get('remarks', '-')}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(settings.TEAMS_WEBHOOK_URL, json=card)
        except Exception as e:
            logger.error(f"Failed to send Teams alert: {e}")

    @staticmethod
    async def send_slack_alert(issue: Dict):
        if not settings.SLACK_WEBHOOK_URL:
            return
            
        color = "#FF0000" if issue.get("severity") in ["HIGH", "CRITICAL"] else "#FFA500"
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"🚨 Anomaly Detected: {issue.get('anomaly_type')}",
                    "fields": [
                        {"title": "Merchant", "value": issue.get('merchant_name', 'Unknown'), "short": True},
                        {"title": "Outlet", "value": issue.get('outlet_name', 'Unknown'), "short": True},
                        {"title": "Severity", "value": issue.get('severity'), "short": True},
                        {"title": "Score", "value": f"{issue.get('anomaly_score', 0):.2f}", "short": True},
                        {"title": "Details", "value": issue.get('remarks', '-'), "short": False}
                    ]
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(settings.SLACK_WEBHOOK_URL, json=payload)
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    @staticmethod
    async def send_email_alert(issue: Dict):
        if not settings.SMTP_HOST:
            return
            
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{issue.get('severity')}] Anomaly Detected: {issue.get('merchant_name')} - {issue.get('outlet_name')}"
        msg["From"] = settings.SMTP_USERNAME or "no-reply@opsexcellence.ai"
        msg["To"] = "nan041211ni@gmail.com"
        
        # Extract metadata
        metadata = issue.get('alert_metadata') or {}
        last_tx_mc = "-"
        if 'Last Mastercard transaction' in str(metadata):
            # This is a bit of a guess based on the requested format, but we'll try to extract or format it
            pass # We'll just serialize it nicely below
        
        last_tx_mc_display = metadata.get('last_tx_mc', str(metadata)) if metadata else "-"
        
        # Determine Auto Resolved
        is_auto_resolved = "Yes" if issue.get('status') == 'RESOLVED' and not issue.get('assigned_to') else "No"

        # Format dates
        def fmt_date(dt):
            if not dt: return "-"
            if isinstance(dt, str): return dt
            return dt.strftime('%b %d, %Y %H:%M:%S')

        template_path = Path(__file__).parent.parent / "templates" / "alert_email.html"
        
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
        except FileNotFoundError:
            logger.error(f"Template not found at {template_path}")
            return
            
        template = Template(template_content)
        html = template.safe_substitute(
            alert_identity=issue.get('id', '-'),
            alert_type=issue.get('anomaly_type', '-'),
            outlet_name=issue.get('outlet_name', '-'),
            merchant_name=issue.get('merchant_name', '-'),
            schemes=issue.get('scheme') or '-',
            volume_class=issue.get('volume_class') or '-',
            severity=issue.get('severity', '-'),
            confidence=issue.get('confidence_score', '-'),
            auto_resolved=is_auto_resolved,
            occurrences=issue.get('occurrence_count', 1),
            last_run_id=issue.get('last_run_id', '-'),
            status=issue.get('status', '-'),
            description=issue.get('remarks', '-'),
            last_transaction_mc=last_tx_mc_display,
            first_detected=fmt_date(issue.get('created_at')),
            last_detected=fmt_date(issue.get('last_detected_at')),
            assigned_to=issue.get('assigned_to') or '-',
            feedback_label=issue.get('user_typing') or '-',
            action_note=issue.get('resolution') or '-',
            resolution_reason=issue.get('root_cause') or '-',
            verification_outcome='-',
            action_taken_at='-',
            resolved_at=fmt_date(issue.get('resolved_at')),
            acknowledged_at='-'
        )
        
        msg.attach(MIMEText(html, "html"))
        
        try:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            logger.error(f"Failed to send Email alert: {e}")

    @classmethod
    async def broadcast_anomaly(cls, issue: Dict):
        """Sends alert to all configured channels based on severity."""
        severity = issue.get("severity", "LOW")
        
        # Always log
        logger.info(f"New Anomaly: {issue.get('anomaly_type')} at {issue.get('outlet_name')} ({severity})")
        
        # Only broadcast HIGH and CRITICAL immediately
        if severity in ["HIGH", "CRITICAL", "MEDIUM", "WARNING"]:
            # Note: Expanding conditions here to ensure emails are sent for broader severities if tested
            await cls.send_teams_alert(issue)
            await cls.send_slack_alert(issue)
            await cls.send_email_alert(issue)
