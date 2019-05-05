from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
import csv

from ..scheduler.models import User
from .models import Room


class RoomBooker:
    def __init__(self):
        if len(sys.argv) > 2:
            num_weeks = int(sys.argv[1])

        self.gcal_helper = GcalHelper(num_weeks)

        matchings = get_matchings()

        # Create the events
        events = []
        for matching in matchings:
            events.append(self.gcal_helper.create_event(matching))

        # Book the events
        for event in events:
            booked, conflicts = self.gcal_helper.book_event(event)

        # Write booked events to csv
        with open("booked_events.csv", "wb") as csv_file:
            fieldnames = ["Timestamp", "EventID"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            for booked_event in booked:
                writer.writerow(booked_event)

        # Post conflicts
        for conflict in conflicts:
            requests.post(
                "http://127.0.0.1:8000/logistinator/conflict/create", data=conflict
            )

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
        title = "CSM Meeting"  ### TODO: Make Matching have a title
        user_id = matching["user_id"]
        room_id = matching["room_id"]
        start = matching["start_datetime"].isoformat()
        end = matching["end_datetime"].isoformat()
        weekly = matching["weekly"]
        timezone = self.gcal_helper.timezone

        invitees = []

        user = User.get_object_or_404(
            pk=user_id
        )  ### TODO: Think about InterviewMatcher
        room = Room.get_object_or_404(pk=room_id)

        # get emails and append
        invitees.append(room.email)
        invitees.append(user.email)

        event = {
            "summary": title,
            "start": {"dateTime": start, "timeZone": timezone},
            "end": {"dateTime": end, "timeZone": timezone},
            "attendees": invitees,
            "weekly": weekly,
        }
        return event


def main():
    RoomBooker()


if __name__ == "__main__":
    main()
