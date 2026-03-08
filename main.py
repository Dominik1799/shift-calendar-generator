import logging
import google_client
import xlsx_client


logging.basicConfig(level=logging.INFO)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Shift Calendar Generator...")
    latest_report_path = google_client.get_latest_shift_report()
    if not latest_report_path:
        logger.info("No new shift reports found. Exiting.")
        exit(0)
    logger.info(f"Latest shift report downloaded to: {latest_report_path}")
    processed_shifts = xlsx_client.process_shift_report(latest_report_path)
    google_client.process_shift_data(processed_shifts)
    logger.info("All shifts processed and calendar events created. Exiting.")
        