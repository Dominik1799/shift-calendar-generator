import os
import json
from dotenv import load_dotenv
load_dotenv() 


EMAIL_USER = os.environ.get("EMAIL_USER", "EMPTY")
EMAIL_PASS = os.environ.get("EMAIL_APP_PASSWORD", "EMPTY")
SUBJECT_KEY_PREFIX = os.environ.get("SUBJECT_KEY_PREFIX", "((shift))")
SAVE_DIRECTORY = os.environ.get("SAVE_DIRECTORY", "./shift-plans")

GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "EMPTY")
GOOGLE_SERVICE_ACCOUNT_JSON: dict = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
print("GOOGLE_SERVICE_ACCOUNT_JSON:", GOOGLE_SERVICE_ACCOUNT_JSON)
GOOGLE_CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID")
GOOGLE_CALENDAR_SHIFT_EVENT_TITLE = os.environ.get("GOOGLE_CALENDAR_SHIFT_EVENT_TITLE", "Janka práca")
# colors accorfing to https://gist.github.com/ansaso/accaddab0892a3b47d5f4884fda0468b#event-colors
GOOGLE_CALENDAR_SHIFT_EVENT_COLOR_ID = os.environ.get("GOOGLE_CALENDAR_SHIFT_EVENT_COLOR_ID", "10")

SHIFT_REPORT_DAY_COLUMN_HEADER = "Deň"
SHIFT_REPORT_PERSON_NAME_COLUMN_HEADER = "Štrbová Jana"