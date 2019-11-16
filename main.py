from __future__ import print_function

import datetime
import iso8601
import pickle
import os.path

from absl import app
from absl import flags
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import logging

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)

FLAGS = flags.FLAGS
flags.DEFINE_list("calendar_names", None, "Names of calendars of interest.")

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def parse_calendar(cal):
    return {k: cal.get(k, None) for k in (
        "id", 
        "summary", 
        "primary", 
        "description", 
        "deleted", 
        "selected")}

def get_calendars(service):
    # Get all the user's calendars
    selected = FLAGS.calendar_names

    calendars = {}
    calendar_list = service.calendarList()

    request = calendar_list.list()
    response = request.execute()

    while True:
        for item in response["items"]:
            if ((selected is None and item.get("selected", False)) 
                or (selected is not None and item["summary"] in selected)):
                calendars[item["summary"]] = item

        # Repeatedly query for more responses
        request = calendar_list.list_next(request, response)
        if request is None:
            break
        response = request.execute()

    return calendars

def format_time(datetime_time):
    """Format time for querying."""
    return datetime_time.isoformat() + 'Z' # 'Z' indicates UTC time

def get_events(service, meta, timenow):
    """Get events from the 7 days from a calendar with the given metadata."""
    events = service.events()

    request = events.list(
        calendarId=meta["id"], 
        timeMin=format_time(timenow - datetime.timedelta(weeks=1)),
        timeMax=format_time(timenow), 
        orderBy="startTime",
        singleEvents=True)
    response = request.execute()
    results = []

    while True:
        results.extend(response["items"])

        # Repeatedly query for more responses
        request = events.list_next(request, response)
        if request is None:
            break
        response = request.execute()
    return results

def sum_time(events):
    """Given a list of events, sum the time taken for all of them."""
    total_time = datetime.timedelta()
    for event in events:
        startTime = iso8601.parse_date(event["start"]["dateTime"])
        endTime = iso8601.parse_date(event["end"]["dateTime"])
        duration = endTime - startTime
        total_time += duration

    # Returns the result in hours
    return total_time.total_seconds() / 60 / 60

def main(argv):
    del argv
    now = datetime.datetime.utcnow()

    service = get_calendar_service()
    calendars_meta = get_calendars(service)

    print("Time per calendar for the last 7 days")
    # TODO: Sort this, display more info, the possibilities are endless...
    for name, meta in calendars_meta.items():
        truncated_name = "{:.15}".format(name)
        events = get_events(service, meta, now)
        total_time = sum_time(events)
        fraction = total_time / 156.0 * 100
        print("  {:15}:\t{:5.2f} h / {:4.1f} %".format(truncated_name, total_time, fraction))

if __name__ == '__main__':
    app.run(main)
