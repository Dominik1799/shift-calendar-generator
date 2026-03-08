import pandas as pd
import settings
import logging
import re
from datetime import datetime


logger = logging.getLogger(__name__)
# we know what is inside each header, not the exact name so we find the exact headers
def __find_correct_headers(first_row) -> tuple[str, str]:
    day_header = None
    person_name_header = None

    for header in first_row:
        if settings.SHIFT_REPORT_DAY_COLUMN_HEADER.lower() in header.lower():
            day_header = header
        if settings.SHIFT_REPORT_PERSON_NAME_COLUMN_HEADER.lower() in header.lower():
            person_name_header = header

    if not day_header or not person_name_header:
        raise ValueError("Could not find the correct headers in the xlsx file.")
    
    return day_header, person_name_header



def process_shift_report(file_path) -> list[dict[str, datetime]]:
    """
    Placeholder function to process the shift report.
    
    Args:
        file_path (str): Path to the xlsx file to process.
    """
    logger.info(f"Processing shift report: {file_path}")
    df = pd.read_excel(file_path)
    # convert nan to normal None for easier handling
    df = df.astype(object).where(pd.notna(df), None) 
    rows_dicts = df.to_dict(orient='records')
    day_header, person_name_header = __find_correct_headers(df.columns)
    date_pattern = r"\b\d{2}\.\d{2}\.\d{4}\b" # matches dates in format dd.mm.yyyy
    time_rage_pattern = r"^(?:[01]\d|2[0-3]):[0-5]\d\s:\s(?:[01]\d|2[0-3]):[0-5]\d$" # matches time ranges in format HH:MM : HH:MM
    time_range_split_pattern = " : "
    shifts_data = []
    for row in rows_dicts:
        date_info = row[day_header]
        time_range = row[person_name_header]
        # if time_range is None, no shift assigned, if date_info doesn't match the pattern, row is irrelevant
        if time_range is None or re.search(date_pattern, str(date_info)) is None:
            continue
        # TODO: create special event for "dovolenka", "Štátny sviatok", "Lekár vlastný" ?
        if re.search(time_rage_pattern, str(time_range)) is None:
            logger.warning(f"Skipping row with unrecognized time range format: {time_range}. Date info: {date_info}")
            continue
        # extract only date from date_info
        date_info = re.search(date_pattern, str(date_info)).group()
        shift_start_time = time_range.split(time_range_split_pattern)[0].strip()
        shift_end_time = time_range.split(time_range_split_pattern)[1].strip()
        shift_start_dt = datetime.strptime(f"{date_info} {shift_start_time}", "%d.%m.%Y %H:%M")
        shift_end_dt = datetime.strptime(f"{date_info} {shift_end_time}", "%d.%m.%Y %H:%M")
        shifts_data.append({
            "start": shift_start_dt,
            "end": shift_end_dt
        })
    logger.info(f"Extracted {len(shifts_data)} shifts from the report.")
    return shifts_data
