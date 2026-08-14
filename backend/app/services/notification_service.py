import httpx
import logging
from typing import Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    async def send_teams_alert(anomaly: Dict):
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
                                "text": f"🚨 Anomaly Detected: {anomaly.get('anomaly_type')}",
                                "weight": "Bolder",
                                "size": "Medium",
                                "color": "Attention" if anomaly.get("severity") in ["HIGH", "CRITICAL"] else "Warning"
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Merchant:", "value": anomaly.get('merchant_name', 'Unknown')},
                                    {"title": "Outlet:", "value": anomaly.get('outlet_name', 'Unknown')},
                                    {"title": "Severity:", "value": anomaly.get('severity')},
                                    {"title": "Score:", "value": f"{anomaly.get('anomaly_score', 0):.2f}"},
                                    {"title": "Details:", "value": anomaly.get('explanation')}
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
    async def send_slack_alert(anomaly: Dict):
        if not settings.SLACK_WEBHOOK_URL:
            return
            
        color = "#FF0000" if anomaly.get("severity") in ["HIGH", "CRITICAL"] else "#FFA500"
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"🚨 Anomaly Detected: {anomaly.get('anomaly_type')}",
                    "fields": [
                        {"title": "Merchant", "value": anomaly.get('merchant_name', 'Unknown'), "short": True},
                        {"title": "Outlet", "value": anomaly.get('outlet_name', 'Unknown'), "short": True},
                        {"title": "Severity", "value": anomaly.get('severity'), "short": True},
                        {"title": "Score", "value": f"{anomaly.get('anomaly_score', 0):.2f}", "short": True},
                        {"title": "Details", "value": anomaly.get('explanation'), "short": False}
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
    async def send_email_alert(anomaly: Dict):
        if not settings.SMTP_HOST or not settings.SMTP_USERNAME:
            return
            
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{anomaly.get('severity')}] Anomaly Detected: {anomaly.get('merchant_name')} - {anomaly.get('outlet_name')}"
        msg["From"] = settings.SMTP_USERNAME
        msg["To"] = "ops-team@example.com" # Should be configurable
        
        text = f"""
        Anomaly Detected
        
        Merchant: {anomaly.get('merchant_name')}
        Outlet: {anomaly.get('outlet_name')}
        Type: {anomaly.get('anomaly_type')}
        Severity: {anomaly.get('severity')}
        Score: {anomaly.get('anomaly_score')}
        
        Explanation:
        {anomaly.get('explanation')}
        """
        
        msg.attach(MIMEText(text, "plain"))
        
        try:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            if settings.SMTP_PASSWORD:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            logger.error(f"Failed to send Email alert: {e}")

    @classmethod
    async def broadcast_anomaly(cls, anomaly: Dict):
        """Sends alert to all configured channels based on severity."""
        severity = anomaly.get("severity", "LOW")
        
        # Always log
        logger.info(f"New Anomaly: {anomaly.get('anomaly_type')} at {anomaly.get('outlet_name')} ({severity})")
        
        # Only broadcast HIGH and CRITICAL immediately
        if severity in ["HIGH", "CRITICAL"]:
            await cls.send_teams_alert(anomaly)
            await cls.send_slack_alert(anomaly)
            await cls.send_email_alert(anomaly)
