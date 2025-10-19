
from dotenv import load_dotenv
import datetime
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict

load_dotenv(override=True)

# Configuration
RECIPIENT_EMAIL = "rammohan3975@gmail.com"

# Email configuration (using Gmail SMTP)
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "rammohan3975@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")  # Gmail App Password

# Mock meeting data for testing
MOCK_MEETINGS = [
    {
        "id": "meet_001",
        "title": "Project Review Meeting",
        "start_time": "2025-10-19T19:00:00",  # 7:00 PM today
        "end_time": "2025-10-19T20:00:00",
        "attendees": [RECIPIENT_EMAIL, "colleague1@example.com"],
        "location": "Conference Room A"
    },
    {
        "id": "meet_002", 
        "title": "Team Standup",
        "start_time": "2025-10-19T20:30:00",  # 8:30 PM today
        "end_time": "2025-10-19T21:00:00",
        "attendees": [RECIPIENT_EMAIL, "team@example.com"],
        "location": "Virtual - Microsoft Teams"
    },
    {
        "id": "meet_003",
        "title": "Client Demo",
        "start_time": "2025-10-19T21:30:00",  # 9:30 PM today
        "end_time": "2025-10-19T23:00:00",
        "attendees": [RECIPIENT_EMAIL, "client@example.com"],
        "location": "Client Office - Madhapur, Hyderabad"
    }
]

def get_hardcoded_weather():
    """Return hardcoded weather data simulating cloudy with expected rain"""
    current_time = datetime.datetime.now()

    weather_data = {
        "location": "Hyderabad, India",
        "current_time": current_time.isoformat(),
        "current_conditions": {
            "temperature_celsius": 28,
            "conditions": "Cloudy with increasing clouds",
            "humidity": 78,
            "cloud_cover": 85,
            "wind_speed_kmh": 15
        },
        "next_6_hours": [
            {"hour": 0, "condition": "Cloudy", "precipitation_probability": 30, "precipitation_mm": 0},
            {"hour": 1, "condition": "Cloudy", "precipitation_probability": 55, "precipitation_mm": 0},
            {"hour": 2, "condition": "Light Rain", "precipitation_probability": 75, "precipitation_mm": 3.2},
            {"hour": 3, "condition": "Heavy Rain", "precipitation_probability": 90, "precipitation_mm": 8.5},
            {"hour": 4, "condition": "Heavy Rain", "precipitation_probability": 85, "precipitation_mm": 6.8},
            {"hour": 5, "condition": "Rain", "precipitation_probability": 70, "precipitation_mm": 4.1}
        ]
    }
    return weather_data

def get_user_meetings(user_email: str = RECIPIENT_EMAIL, hours_ahead: int = 6):
    """Get meetings for the next N hours for a user"""
    current_time = datetime.datetime.now()
    end_time = current_time + datetime.timedelta(hours=hours_ahead)

    relevant_meetings = []
    for meeting in MOCK_MEETINGS:
        meeting_start = datetime.datetime.fromisoformat(meeting["start_time"])
        if current_time <= meeting_start <= end_time:
            if user_email in meeting["attendees"]:
                relevant_meetings.append(meeting)

    return relevant_meetings

def analyze_weather_impact(weather_data: Dict, meetings: List[Dict]):
    """Analyze if weather will impact meetings"""
    alerts = []
    current_time = datetime.datetime.now()

    for hour_data in weather_data["next_6_hours"]:
        hour_num = hour_data["hour"]
        precip_prob = hour_data["precipitation_probability"]
        precipitation = hour_data["precipitation_mm"]
        condition = hour_data["condition"]

        is_severe = precip_prob > 60 or precipitation > 2.0 or "Rain" in condition

        if is_severe:
            impact_time = current_time + datetime.timedelta(hours=hour_num)

            for meeting in meetings:
                meeting_start = datetime.datetime.fromisoformat(meeting["start_time"])
                meeting_end = datetime.datetime.fromisoformat(meeting["end_time"])

                if meeting_start <= impact_time <= meeting_end or \
                   (impact_time <= meeting_start <= (impact_time + datetime.timedelta(hours=1))):

                    alert = {
                        "meeting": meeting,
                        "weather_condition": condition,
                        "impact_time": impact_time.strftime("%I:%M %p"),
                        "precipitation_prob": precip_prob,
                        "precipitation_mm": precipitation,
                        "is_physical_location": "Virtual" not in meeting["location"] and "Teams" not in meeting["location"]
                    }

                    if not any(a["meeting"]["id"] == meeting["id"] for a in alerts):
                        alerts.append(alert)

    return alerts

def send_email_notification(subject: str, body_text: str, body_html: str):
    """Send email notification"""

    # Print to console
    print("\n" + "="*70)
    print(f"📧 EMAIL NOTIFICATION TO: {RECIPIENT_EMAIL}")
    print("="*70)
    print(body_text)
    print("="*70 + "\n")

    # Send actual email if credentials are configured
    if SENDER_PASSWORD:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECIPIENT_EMAIL

            # Attach both text and HTML versions
            part1 = MIMEText(body_text, 'plain')
            part2 = MIMEText(body_html, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send via Gmail SMTP
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)

            print("✅ Email notification sent successfully!")

        except Exception as e:
            print(f"❌ Error sending email: {e}")
            print("💡 Email preview shown above (console output)")
    else:
        print("⚠️  Email credentials not configured in .env file")
        print("   Notification displayed above (console only)")
        print("\n💡 TO SEND ACTUAL EMAILS:")
        print("   1. Enable 2-Factor Authentication on your Gmail account")
        print("   2. Generate an App Password: https://myaccount.google.com/apppasswords")
        print("   3. Add to .env file:")
        print("      SENDER_EMAIL=rammohan3975@gmail.com")
        print("      SENDER_APP_PASSWORD=your_16_char_app_password")

def format_alert_message(alerts: List[Dict], weather_data: Dict):
    """Format weather alert message for email"""

    current_weather = weather_data["current_conditions"]
    location = weather_data["location"]
    current_time = datetime.datetime.now().strftime("%I:%M %p, %B %d, %Y")

    # Plain text version
    text_parts = [
        f"WEATHER BUDDY ALERT",
        f"Generated at: {current_time}",
        f"Location: {location}\n",
        f"CURRENT CONDITIONS:",
        f"• Weather: {current_weather['conditions']}",
        f"• Temperature: {current_weather['temperature_celsius']}°C",
        f"• Humidity: {current_weather['humidity']}%",
        f"• Cloud Cover: {current_weather['cloud_cover']}%\n",
        f"FORECAST: Rain expected in next 2-4 hours\n",
        f"=" * 50,
        f"MEETINGS AFFECTED BY WEATHER\n"
    ]

    for i, alert in enumerate(alerts, 1):
        meeting = alert["meeting"]
        meeting_time = datetime.datetime.fromisoformat(meeting["start_time"])

        text_parts.append(f"{i}. {meeting['title']}")
        text_parts.append(f"   Time: {meeting_time.strftime('%I:%M %p')}")
        text_parts.append(f"   Location: {meeting['location']}")
        text_parts.append(f"   Weather: {alert['weather_condition']} expected around {alert['impact_time']}")
        text_parts.append(f"   Rain Probability: {alert['precipitation_prob']}%")

        if alert["is_physical_location"]:
            next_slot = (meeting_time + datetime.timedelta(hours=2)).strftime('%I:%M %p')
            text_parts.append(f"   ⚠️ RECOMMENDATION: Consider rescheduling to {next_slot} or make it virtual")
        else:
            text_parts.append(f"   ✅ NO ACTION NEEDED: Virtual meeting not affected by weather")

        text_parts.append("")

    text_parts.extend([
        "=" * 50,
        "Weather Buddy Agent - Your AI meeting assistant",
        "Keeping you productive rain or shine!"
    ])

    text_message = "\n".join(text_parts)

    # HTML version
    html_message = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
          .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
          .weather-box {{ background: #f7fafc; border-left: 4px solid #4299e1; 
                         padding: 15px; margin: 15px 0; border-radius: 4px; }}
          .meeting-card {{ background: white; border: 1px solid #e2e8f0; 
                          padding: 15px; margin: 10px 0; border-radius: 8px; 
                          box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
          .alert {{ background: #fff5f5; border-left: 4px solid #f56565; padding: 10px; margin: 10px 0; }}
          .success {{ background: #f0fff4; border-left: 4px solid #48bb78; padding: 10px; margin: 10px 0; }}
          .icon {{ font-size: 24px; margin-right: 10px; }}
          .footer {{ text-align: center; color: #718096; padding: 20px; margin-top: 30px; 
                    border-top: 1px solid #e2e8f0; }}
        </style>
      </head>
      <body>
        <div class="header">
          <h1>🌧️ Weather Buddy Alert</h1>
          <p>Meeting Impact Notification</p>
          <small>{current_time}</small>
        </div>

        <div class="weather-box">
          <h2>☁️ Current Weather - {location}</h2>
          <p><strong>Conditions:</strong> {current_weather['conditions']}<br>
          <strong>Temperature:</strong> {current_weather['temperature_celsius']}°C<br>
          <strong>Humidity:</strong> {current_weather['humidity']}%<br>
          <strong>Cloud Cover:</strong> {current_weather['cloud_cover']}%</p>
          <p><strong>🌧️ Forecast:</strong> Rain expected in next 2-4 hours</p>
        </div>

        <h2>📅 Meetings Affected by Weather</h2>
    """

    for i, alert in enumerate(alerts, 1):
        meeting = alert["meeting"]
        meeting_time = datetime.datetime.fromisoformat(meeting["start_time"])
        next_slot = (meeting_time + datetime.timedelta(hours=2)).strftime('%I:%M %p')

        card_class = "alert" if alert["is_physical_location"] else "success"

        html_message += f"""
        <div class="meeting-card">
          <h3>{i}. {meeting['title']}</h3>
          <p><strong>⏰ Time:</strong> {meeting_time.strftime('%I:%M %p')}<br>
          <strong>📍 Location:</strong> {meeting['location']}<br>
          <strong>🌦️ Weather Impact:</strong> {alert['weather_condition']} expected around {alert['impact_time']}<br>
          <strong>💧 Rain Probability:</strong> {alert['precipitation_prob']}%</p>

          <div class="{card_class}">
        """

        if alert["is_physical_location"]:
            html_message += f"""
            <strong>⚠️ RECOMMENDATION:</strong> Consider rescheduling to {next_slot} or make it virtual
            """
        else:
            html_message += f"""
            <strong>✅ NO ACTION NEEDED:</strong> Virtual meeting not affected by weather
            """

        html_message += """
          </div>
        </div>
        """

    html_message += """
        <div class="footer">
          <p><strong>Weather Buddy Agent</strong><br>
          Your AI-powered meeting assistant<br>
          Keeping you productive rain or shine! ☔</p>
        </div>
      </body>
    </html>
    """

    return text_message, html_message

def run_weather_buddy_check():
    """Main function to run weather check and send alerts"""

    print("🤖 Weather Buddy Agent Starting...")
    print(f"⏰ Current Time: {datetime.datetime.now().strftime('%I:%M %p, %B %d, %Y')}")
    print(f"👤 Monitoring meetings for: {RECIPIENT_EMAIL}\n")

    # Get hardcoded weather data
    weather_data = get_hardcoded_weather()
    print(f"🌤️  Current Weather: {weather_data['current_conditions']['conditions']}, {weather_data['current_conditions']['temperature_celsius']}°C")
    print(f"🌧️  Rain Forecast: Expected in 2-4 hours\n")

    # Get upcoming meetings
    meetings = get_user_meetings(RECIPIENT_EMAIL, 6)
    print(f"📅 Found {len(meetings)} meetings in next 6 hours:")
    for meeting in meetings:
        meeting_time = datetime.datetime.fromisoformat(meeting["start_time"])
        print(f"   - {meeting['title']} at {meeting_time.strftime('%I:%M %p')} ({meeting['location']})")
    print()

    if not meetings:
        print("✅ No meetings scheduled - no weather impact to report")
        return

    # Analyze weather impact
    alerts = analyze_weather_impact(weather_data, meetings)

    if alerts:
        print(f"⚠️  Weather will impact {len(alerts)} meeting(s)!\n")

        # Format and send notification
        text_message, html_message = format_alert_message(alerts, weather_data)
        subject = f"🌧️ Weather Alert: {len(alerts)} Meeting(s) May Be Affected"

        send_email_notification(subject, text_message, html_message)

        print("✅ Weather Buddy check completed!")
    else:
        print("✅ No significant weather impact on meetings")

if __name__ == "__main__":
    run_weather_buddy_check()
