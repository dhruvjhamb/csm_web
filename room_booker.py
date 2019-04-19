from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
from csm_web/scheduler/.models import User, Room

# If modifying these scopes, delete the file token.pickle.
SCOPES = 'https://www.googleapis.com/auth/calendar'
TIMEZONE = 'America/Los_Angeles'
CALENDAR_ID = 'primary'
NUM_WEEKS = 10


def gcal_api_authenticate():
    """Google Calendar Authentication. Returns the service object to be used
    for making calls to the api."""
    # token.json stores the user's access and refresh tokens. It is created 
    # automatically when the authorization flow completes for the first time.

    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('secrets/credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))
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

    # get emails and append

    invitees.append()
    invitees.append()

    event = {
        'summary': title,
        'start': {
            'dateTime': start,
            'timeZone': timezone
        },
        'end': {
            'dateTime': end,
            'timeZone': timezone
        },
        'attendees': invitees
    }

    if weekly:
        rule = f'RRULE:FREQ=WEEKLY;COUNT={NUM_WEEKS}'
        event['recurrence'] = [rule]


def is_room_free(event, service):
    start = event['start']['dateTime']
    end = event['end']['dateTime']
    room_email = event['attendees']

    timeMin = start.isoformat()
    timeMax = end.isoformat()
    
    # Start and End are already time zone aware
    # However, a timezone must be provided to ensure that the
    # result is directly translated too.
    timeZone = TIMEZONE  
    items = [{'id': room_email}]

    freebusy_query = {
        'timeMin': timeMin,
        'timeMax': timeMax,
        'timeZone': timeZone,
        'items': items
    }

    result = service.freebusy().query(body=freebusy_query).execute()
    booked_events = result['calendars'][room_email]['busy']
    return len(booked_events)


def book_event(event, service):
    """Takes in an event object as per the specification of Google Calendar's API,
    and books it."""

    ### CHECK IF CONCLICT
    ### FREE BUSY METHOD in google calendar
    """
    deal with weekly conflicts
    timezone issues - make everything non-time until actually booking
    """
    if is_room_free(event, service) != 0:
        # make post request to conflict

    event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    storage_data = {'Timestamp': datetime.datetime.now(),'EventID': event['id']}
    return storage_data


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
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
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)


    # Call the Calendar API
    matchings = get_matchings()

    service = gcal_api_authenticate()

    events = []
    for matching in matchings:
        events.append(create_event(row))

    # Book the events
    for event in events:
        storage_data = book_event(event, service)

if __name__ == '__main__':
    main()