from Event import Event

class Day():
    def __init__(self, dateString, dataDict):
        self.date = dateString
        self.events = [Event(event) for event in dataDict['events']]
    def addEvent(self, eventDict):
        self.events.append(Event(eventDict))
    def deletEvent(self, eventIndex):
        self.events.pop(eventIndex)
    def jsonify(self):
        return {
            "date": self.date,
            "events": [event.jsonify() for event in self.events]
        }
    def listView(self, pointedEvent=None, tag=None):
        eventListStr = "\n".join([event.listView(arrow=pointedEvent==idx) for idx, event in enumerate(self.events) if tag in event.tags or tag is None])
        return f"""==== {self.date} ====
{eventListStr}
====={"="*len(self.date)}====="""
    def detailedView(self, tag=None, hideDone=False):
        eventListStr = "\n\n".join([event.detailedView(idx=idx+1) for idx, event in enumerate(self.events) if (tag in event.tags or tag is None) and not (hideDone and event.status)])
        return f"""==== {self.date} ====
{eventListStr}
====={"="*len(self.date)}====="""
    def calendarView(self, outputLength=15, tag=None):
        return [event.shorten(outputLength) for event in self.events if tag in event.tags or tag is None]
