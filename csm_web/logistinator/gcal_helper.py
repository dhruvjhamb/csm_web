class GcalHelper:

	def __init__(self, num_weeks):
		self.num_weeks = num_weeks
		self.scopes = "https://www.googleapis.com/auth/calendar"
		self.timezone = "America/Los_Angeles"
		self.calendar_id = "primary"
		self.service = gcal_api_authenticate()

	def gcal_api_authenticate():
	    """Google Calendar Authentication. Returns the service object to be used
	    for making calls to the api."""
	    # token.json stores the user's access and refresh tokens. It is created
	    # automatically when the authorization flow completes for the first time.

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
    	return service


	def is_room_free(event, timedelta=None):
		""" Checks if booking event will create conflict.
			Assumes that the first attendee of event["attendees"] is room email.
		"""
		if not timedelta:
			timedelta = datetime.timedelta(days=0)

	    start = event["start"]["dateTime"]
	    end = event["end"]["dateTime"]
	    # The first element is room email
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

	    result = self.service.freebusy().query(body=freebusy_query).execute()
	    booked_events += result["calendars"][room_email]["busy"]
	    return len(booked_events) == 0


	def is_room_free_weekly(event):
		""" Checks if booking a recurring event will create conflict.
			Ensure that the first attendee in event["attendees"] is the room email.
		"""

		return all([is_room_free(event, datetime.timedelta(days=7*i) for i in range(self.num_weeks))])


	def book_event(event):
	    """Takes in an event object as per the specification of Google Calendar's API,
	    and books it.

	    deal with weekly conflicts
	    timezone issues - make everything non-time until actually booking
	    """
	    storage_data = []
	    conflicts = []

	    if is_room_free_weekly(event) == 0 and event["weekly"]:
	        rule = f"RRULE:FREQ=WEEKLY;COUNT={self.num_weeks}"
	        event["recurrence"] = [rule]

	        event = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
	        storage_data.append({"Timestamp": datetime.datetime.now(), "EventID": event["id"]})
	        
	    elif event["weekly"]:

	        i = 0

	        while i < self.num_weeks:
	            d = datetime.timedelta(days=7 * i)

	            if not is_room_free(event, d):

	                user_id = event["attendees"][1]
	                room_id = event["attendees"][0]
	                start_datetime = event["start"]["dateTime"]
	                end_datetime = event["end"]["dateTime"]
	                data={
	                        "user_id": user_id,
	                        "room_id": room_id,
	                        "start_datetime": start_datetime,
	                        "end_datetime": end_datetime,
	                    }
	                conflicts.append(data)
	            else:
	                event = (
	                    self.service.events()
	                    .insert(calendarId=self.calendar_id, body=event)
	                    .execute()
	                )
	                storage_data.append({
	                    "Timestamp": datetime.datetime.now(),
	                    "EventID": event["id"],
	                })
	            i += 1

	        
	    elif not is_room_free(event):

        
        	user_id = event["attendees"][1]
            room_id = event["attendees"][0]
            start_datetime = event["start"]["dateTime"]
            end_datetime = event["end"]["dateTime"]
            data={
                    "user_id": user_id,
                    "room_id": room_id,
                    "start_datetime": start_datetime,
                    "end_datetime": end_datetime,
                }
            conflicts.append(data)
	        	
        else:
	        event = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
	        storage_data.append({"Timestamp": datetime.datetime.now(), "EventID": event["id"]})
		        

        return storage_data, conflicts