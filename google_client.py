import imaplib
import email
import os
import logging
import pytz
from datetime import datetime, timedelta

import settings

from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def get_latest_shift_report():
    """
    Finds and downloads the latest shift report from unread emails.
    
    Returns:
        str: Path to the downloaded xlsx file, or None if nothing was found
    """
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(settings.EMAIL_USER, settings.EMAIL_PASS)
        mail.select("inbox")
        logger.info("Successfully connected and logged in to the email server.")

        # Find unread emails
        status, messages = mail.search(None, 'UNSEEN')

        for num in messages[0].split():
            status, data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            
            subject = msg["Subject"]
            sender = msg["From"]
            date_received = msg["Date"]
            logger.info(f"Processing email: {subject} | From: {sender} | Received: {date_received}")

            # 1. Check if Subject matches prefix
            if subject.lower().strip().startswith("((shift))"):
                logger.info(f"Subject match: '{subject}' from {sender} (received: {date_received})")

                # 2. Iterate through email parts
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue

                    filename = part.get_filename()
                    
                    # 3. Check if it's an .xlsx file
                    if filename and filename.lower().endswith('.xlsx'):
                        os.makedirs(settings.SAVE_DIRECTORY, exist_ok=True)
                        filepath = os.path.join(settings.SAVE_DIRECTORY, filename)
                        
                        try:
                            with open(filepath, 'wb') as f:
                                f.write(part.get_payload(decode=True))
                            logger.info(f"Successfully downloaded: {filename}")
                            
                            # Mark as read and return
                            mail.store(num, '+FLAGS', '\\Seen')
                            mail.logout()
                            logger.info("Session closed.")
                            # currently this works only for one file per mail
                            return filepath
                        except Exception as e:
                            logger.error(f"Failed to save {filename}: {e}")

            # Mark as read
            mail.store(num, '+FLAGS', '\\Seen')

        mail.logout()
        logger.info("Session closed.")
        return None
        
    except Exception as e:
        logger.exception(f"An error occurred during execution. Exitting.")
        exit(1)


def process_shift_data(shift_data: list[dict[str, datetime]]):
    """
    Process the shift data and create calendar events.
    
    Workflow:
    1. Extract the month from the first shift
    2. Delete all matching calendar events for that month
    3. Create new events for all shifts
    
    This workflow allow us to ensure shifts reschedules are accounted for without creating duplicate events
    
    Args:
        shift_data (list[dict[str, datetime]]): List of shifts with start and end datetimes.
    """
    if not shift_data:
        logger.warning("No shift data to process.")
        return
    
    # Extract month from first shift
    first_shift_date = shift_data[0]["start"]
    month_year = (first_shift_date.year, first_shift_date.month)
    logger.info(f"Processing shifts for month: {month_year[0]}-{month_year[1]:02d}")
    
    # Delete all matching events for the extracted month
    __delete_month_events(first_shift_date.year, first_shift_date.month)
    
    # Create new events for all shifts
    for shift in shift_data:
        __create_calendar_event(
            date_time_start=shift["start"].isoformat(),
            date_time_end=shift["end"].isoformat()
        )


def __delete_month_events(year: int, month: int, timezone_str="Europe/Bratislava"):
    """
    Delete all calendar events matching the configured event title for a given month.
    
    Args:
        year (int): Year of the month
        month (int): Month (1-12)
        timezone_str (str): Timezone name, default "Europe/Bratislava"
    """
    logger.info(f"Deleting existing events for month: {year}-{month:02d}")
    # Setup API ---
    credentials = service_account.Credentials.from_service_account_info(
        settings.GOOGLE_SERVICE_ACCOUNT_JSON,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    service = build("calendar", "v3", credentials=credentials)
    
    # Month range ---
    tz = pytz.timezone(timezone_str)
    month_start = tz.localize(datetime(year, month, 1, 0, 0, 0))
    if month == 12:
        month_end = tz.localize(datetime(year + 1, 1, 1, 0, 0, 0))
    else:
        month_end = tz.localize(datetime(year, month + 1, 1, 0, 0, 0))
    
    month_start_str = month_start.isoformat()
    month_end_str = month_end.isoformat()
    
    # Find and delete all matching events in the month ---
    events_result = service.events().list(
        calendarId=settings.GOOGLE_CALENDAR_ID,
        timeMin=month_start_str,
        timeMax=month_end_str,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    
    events = events_result.get("items", [])
    deleted_count = 0
    
    for event in events:
        if event.get("summary") == settings.GOOGLE_CALENDAR_SHIFT_EVENT_TITLE:
            logger.info(f"Deleting event for date: {event['start'].get('dateTime', event['start'].get('date'))}")
            service.events().delete(calendarId=settings.GOOGLE_CALENDAR_ID, eventId=event["id"]).execute()
            deleted_count += 1
    
    logger.info(f"Deleted {deleted_count} event(s) for {year}-{month:02d}")


def __create_calendar_event(date_time_start, date_time_end, timezone_str="Europe/Bratislava"):
    """
    Create a Google Calendar event for a given time range.
    
    Args:
        date_time_start (str): Event start time in ISO format, e.g. "2026-03-08T09:00:00"
        date_time_end (str): Event end time in ISO format, e.g. "2026-03-08T17:00:00"
        timezone_str (str): Timezone name, default "Europe/Bratislava"
    """
    # Setup API ---
    credentials = service_account.Credentials.from_service_account_info(
        settings.GOOGLE_SERVICE_ACCOUNT_JSON,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    service = build("calendar", "v3", credentials=credentials)
    
    # Timezone-aware datetime objects ---
    tz = pytz.timezone(timezone_str)
    start_dt = tz.localize(datetime.fromisoformat(date_time_start))
    end_dt = tz.localize(datetime.fromisoformat(date_time_end))
    
    # --- Create new event ---
    shift_event = {
        "summary": settings.GOOGLE_CALENDAR_SHIFT_EVENT_TITLE,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": timezone_str},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": timezone_str},
        "colorId": settings.GOOGLE_CALENDAR_SHIFT_EVENT_COLOR_ID
    }
    
    inserted_event = service.events().insert(calendarId=settings.GOOGLE_CALENDAR_ID, body=shift_event).execute()
    logger.info(f"Created shift event for date: {start_dt.date()}")