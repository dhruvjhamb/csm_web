from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests

from .models import User, Room
from .scheduler import Dir
from csm_web/scheduler/.models import User, Room

# If modifying these scopes, delete the file token.pickle.
SCOPES = "https://www.googleapis.com/auth/calendar"
TIMEZONE = "America/Los_Angeles"
CALENDAR_ID = "primary"
NUM_WEEKS = 10


def gcal_api_authenticate():
    """Google Calendar Authentication. Returns the service object to be used
    for making calls to the api."""
    # token.json stores the user's access and refresh tokens. It is created
    # automatically when the authorization flow completes for the first time.

    store = file.Storage("token.json")
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets("secrets/credentials.json", SCOPES)
        creds = tools.run_flow(flow, store)
    service = build("calendar", "v3", http=creds.authorize(Http()))
    return service


def get_matchings():
    """Call the endpoint to get the matchings, where each matching is a dictionary.
    """
    get_matchings_url = "http://127.0.0.1:8000/logistinator/matching/get_all"

    r = requests.get(get_matchings_url)
    return r.content


def create_event(matching):
    """Creates an 'event' dictionary object as required by Google Calendar's
    API, and returns it.
    """
    title = "CSM Meeting"
    user_id = matching["user_id"]
    room_id = matching["room_id"]
    start = matching["start_datetime"].isoformat()
    end = matching["end_datetime"].isoformat()
    weekly = matching["weekly"]
    timezone = TIMEZONE

    invitees = []

    user = User.get_object_or_404(pk=user_id)
    room = Room.get_object_or_404(pk=room_id)

    ### get emails and append

    invitees.append(room.email)
    invitees.append(user.email)

    event = {
        "summary": title,
        "start": {"dateTime": start, "timeZone": timezone},
        "end": {"dateTime": end, "timeZone": timezone},
        "attendees": invitees,
        "weekly": weekly,
    }


def is_room_free(event, service, timedelta):
    start = event["start"]["dateTime"]
    end = event["end"]["dateTime"]
    room_email = event["attendees"][0]

    timeMin = start.isoformat()
    timeMax = end.isoformat()

    # Start and End are already time zone aware
    # However, a timezone must be provided to ensure that the
    # result is directly translated too.
    timeZone = TIMEZONE
    items = [{"id": room_email}]

    freebusy_query = {
        "timeMin": timeMin + timedelta,
        "timeMax": timeMax + timedelta,
        "timeZone": timeZone,
        "items": items,
    }

    result = service.freebusy().query(body=freebusy_query).execute()
    booked_events += result["calendars"][room_email]["busy"]
    return len(booked_events)


def is_room_free_weekly(event, service):
    start = event["start"]["dateTime"]
    end = event["end"]["dateTime"]
    room_email = event["attendees"][0]

    timeMin = start.isoformat()
    timeMax = end.isoformat()

    # Start and End are already time zone aware
    # However, a timezone must be provided to ensure that the
    # result is directly translated too.
    timeZone = TIMEZONE
    items = [{"id": room_email}]

    i = 0
    count = 0

    while i < NUM_WEEKS:
        d = datetime.timedelta(days=count)
        i += 1
        count += 7

        freebusy_query = {
            "timeMin": timeMin + d,
            "timeMax": timeMax + d,
            "timeZone": timeZone,
            "items": items,
        }

        result = service.freebusy().query(body=freebusy_query).execute()
        booked_events += result["calendars"][room_email]["busy"]
        if len(booked_events) != 0:
            return False

    return True


def book_event(event, service):
    """Takes in an event object as per the specification of Google Calendar's API,
    and books it.

    deal with weekly conflicts
    timezone issues - make everything non-time until actually booking
    """
    storage_data = {}

    if is_room_free_weekly(event, service) == 0 and event["weekly"]:
        rule = f"RRULE:FREQ=WEEKLY;COUNT={NUM_WEEKS}"
        event["recurrence"] = [rule]

        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        storage_data = {"Timestamp": datetime.datetime.now(), "EventID": event["id"]}
        return storage_data
    elif event["weekly"]:

        i = 0
        count = 0

        while i < NUM_WEEKS:
            d = datetime.timedelta(days=count)

            if is_room_free(event, service, d) != 0:

                user_id = event["attendees"][1]
                room_id = event["attendees"][0]
                start_datetime = event["start"]["dateTime"]
                end_datetime = event["end"]["dateTime"]

                requests.post(
                    "http://127.0.0.1:8000/logistinator/conflict/create",
                    data={
                        "user_id": user_id,
                        "room_id": room_id,
                        "start_datetime": start_datetime,
                        "end_datetime": end_datetime,
                    },
                )
            else:
                event = (
                    service.events()
                    .insert(calendarId=CALENDAR_ID, body=event)
                    .execute()
                )
                storage_data += {
                    "Timestamp": datetime.datetime.now(),
                    "EventID": event["id"],
                }
            i += 1
            count += 7

        return storage_data
    else:

        if is_room_free(event, service) != 0:

            ### Need to fix this post request

            requests.post("http://127.0.0.1:8000/logistinator/conflict/create")

        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        storage_data = {"Timestamp": datetime.datetime.now(), "EventID": event["id"]}
        return storage_data


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    matchings = get_matchings()

    service = gcal_api_authenticate()

    events = []
    for matching in matchings:
        events.append(create_event(row))

    # Book the events
    for event in events:
        storage_data = book_event(event, service)


if __name__ == "__main__":
    main()
