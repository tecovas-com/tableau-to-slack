from dotenv import load_dotenv
import json
import logging
import os
import requests
from datetime import datetime
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

load_dotenv()

# CONSTANTS
HOLIDAY_GOAL_METER_TRACKER = "aedd0a26-f81d-4928-8a8d-974835f067eb"  # HOLIDAY GOAL METER TRACKER
BFCM_DASHBOARD = "6d9631f8-8d0f-45cd-8c0a-edf13e618680"  # BFCM DASHBOARD
SLACK_CHANNEL_NAME = "tableau-testing"
SLACK_CHANNEL_ID = "C09U8MTJ0CA"

# ENVIRONMENT VARIABLES
TABLEAU_HOST = os.getenv("TABLEAU_HOST")
TABLEAU_API_VERSION = os.getenv("TABLEAU_API_VERSION")
TABLEAU_PAT_NAME = os.getenv("TABLEAU_PAT_NAME")
TABLEAU_PAT_SECRET = os.getenv("TABLEAU_PAT_SECRET")
TABLEAU_SITE_ID = os.getenv("TABLEAU_SITE_ID")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")


def get_tableau_auth_token() -> str:
    """
    Authenticates with the Tableau Server using a personal access token (PAT)
    and returns an authentication token.
    """
    logger.info("Retrieving Tableau auth token...")
    url = f"{os.getenv('TABLEAU_HOST')}/api/{os.getenv('TABLEAU_API_VERSION')}/auth/signin"

    payload = json.dumps(
        {
            "credentials": {
                "personalAccessTokenName": os.getenv("TABLEAU_PAT_NAME"),
                "personalAccessTokenSecret": os.getenv("TABLEAU_PAT_SECRET"),
                "site": {"contentUrl": "tecovas"},
            }
        }
    )
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    logger.info("Tableau auth token retrieved successfully.")
    return response.json()["credentials"]["token"]


def get_dashboard_image(token: str, dashboard_id: str) -> bytes:
    """
    Fetches the image of the specified Tableau dashboard using the provided
    authentication token.
    """
    logger.info(f"Fetching Tableau dashboard {dashboard_id} image...")
    url = (
        f"{os.getenv('TABLEAU_HOST')}/api/{os.getenv('TABLEAU_API_VERSION')}/sites/"
        f"{os.getenv('TABLEAU_SITE_ID')}/views/{dashboard_id}/image?maxAge=0"
    )

    payload = {}
    headers = {"Accept": "application/json", "X-Tableau-Auth": token}
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code != 200:
        logger.error(f"Failed to fetch dashboard image: {response.status_code} — {response.text}")
        logger.debug(f"Request headers: {response.request.headers}")
        raise Exception(f"Error fetching dashboard image: {response.status_code} — {response.text}")
    logger.info("Tableau dashboard image fetched successfully.")
    return response.content


def post_image_to_slack(
        image_bytes: bytes,
        channel: str,
        text: str,
        title: str
) -> None:
    """
    Uploads an image to Slack and posts it to a specified channel.

    Args:
        image_bytes (bytes): The binary content of the image to upload.
        channel (str): The Slack channel ID where the image will be posted.
        text (str): The text to accompany the image in the post.
        title (str): The title of the image file.

    Steps:
    1. Get an upload URL from Slack.
    2. Upload the image bytes to the returned URL.
    """
    logger.info(f"Posting image to Slack channel {channel}...")
    # Step 1: Get upload URL from Slack
    upload_url_resp = requests.post(
        "https://slack.com/api/files.getUploadURLExternal",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        data={"filename": "dashboard.png", "length": str(len(image_bytes))},
    )
    upload_url_json = upload_url_resp.json()

    if not upload_url_json.get("ok"):
        raise Exception(f"Error getting upload URL: {upload_url_json}")

    upload_url = upload_url_json["upload_url"]
    file_id = upload_url_json["file_id"]

    # Step 2: Upload binary content directly to the returned URL
    upload_resp = requests.post(
        upload_url,
        headers={"Content-Type": "application/octet-stream"},
        data=image_bytes,
    )

    if upload_resp.status_code != 200:
        raise Exception(
            f"Error uploading file: {upload_resp.status_code} — {upload_resp.text}"
        )

    # Step 3: Share in channel
    complete_resp = requests.post(
        "https://slack.com/api/files.completeUploadExternal",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        json={
            "files": [
                {"id": file_id, "title": title}
            ],
            "channel_id": channel,
            "initial_comment": text,
        },
    )
    complete_json = complete_resp.json()

    if not complete_json.get("ok"):
        raise Exception(f"Error completing upload: {complete_json}")

    logger.info(f"Uploaded image to Slack channel {channel}")
    return complete_json


if __name__ == "__main__":
    token = get_tableau_auth_token()
    cst = pytz.timezone('America/Chicago')
    current_time = datetime.now(cst).strftime('%m-%d %H:%M')

    # BFCM DASHBOARD
    image = get_dashboard_image(token, BFCM_DASHBOARD)
    post_image_to_slack(image, SLACK_CHANNEL_ID, f"⚫💰 BFCM Dashboard Update - {current_time}", "BFCM Dashboard")

    # HOLIDAY GOAL METER TRACKER
    image = get_dashboard_image(token, HOLIDAY_GOAL_METER_TRACKER)
    post_image_to_slack(image, SLACK_CHANNEL_ID, f"🎅🎄🎁 Holiday Goal Meter Tracker Update - {current_time}", "Holiday Goal Meter Tracker")