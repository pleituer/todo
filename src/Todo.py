import os
import json
import copy
import datetime

from Day import Day
from config import CONFIG
from utils import TODAY

class Todo():
    def __init__(self, fp=None):
        if fp is None:
            self.data = {}
            self.numOfEvents = []
        else:
            with open(fp, "r") as f:
                self.data = json.load(f)
            self.data = {date: Day(date, self.data[date]) for date in self.data if not date.startswith("-")}
            self.numOfEvents = [len(self.data[date].events) for date in self.data]
        self.outputLength = int(CONFIG["outputLength"])
        self.ntask = int(CONFIG["ntask"])
        # archieve old tasks
        if os.path.exists(CONFIG["archivePath"]):
            with open(CONFIG["archivePath"], "r") as f:
                archieved = {date:Day(date, day) for date, day in json.load(f).items()}
                for date in self.data:
                    if date < TODAY:
                        archieved[date] = copy.deepcopy(self.data[date])
        else:
            archieved = {date: copy.deepcopy(self.data[date]) for date in self.data if date < TODAY}
        # self.data only contains TODAY and future tasks
        self.data = {date: self.data[date] for date in self.data if date >= TODAY}
        if CONFIG["autoAddUncompletedTasks"]:
            for date in archieved:
                if date < TODAY:
                    for event in archieved[date].events:
                        if not event.status and "-done-" not in event.tags:
                            jsonifiedEvent = copy.deepcopy(event.jsonify())
                            jsonifiedEvent["tags"].insert(0, "-overdue-")
                            jsonifiedEventDone = copy.deepcopy(jsonifiedEvent)
                            jsonifiedEventDone["status"] = True
                            if not (TODAY in self.data and (jsonifiedEvent in self.data[TODAY].jsonify()["events"] or jsonifiedEventDone in self.data[TODAY].jsonify()["events"])):
                                self.addEvent(TODAY, jsonifiedEvent)
                            elif not (TODAY in self.data and jsonifiedEvent in self.data[TODAY].jsonify()["events"]):
                                event.tags.append("-done-")
        with open(CONFIG["archivePath"], "w") as f:
            json.dump({date:archieved[date].jsonify() for date in archieved}, f)
    def save(self, fp):
        with open(fp, "w") as f:
            sterializedData = {date: self.data[date].jsonify() for date in self.data}
            json.dump(sterializedData, f)
    def addEvent(self, dateString, dataDict):
        day = self.data.get(dateString, None)
        if day is None:
            self.data[dateString] = Day(dateString, {'events': [dataDict]})
        else:
            day.addEvent(dataDict)
        self.data = {date: self.data[date] for date in sorted(self.data)}
        self.numOfEvents = [len(self.data[date].events) for date in self.data]
    def deleteEvent(self, dateString, eventIndex):
        try: 
            self.data[dateString].deletEvent(eventIndex)
            if len(self.data[dateString].events) == 0:
                self.data.pop(dateString)
        except:
            print("Invalid Date or Index")
        self.numOfEvents = [len(self.data[date].events) for date in self.data]
    def listView(self, day=None, pointer=None, tag=None):
        for d in self.data: self.data[d].events = sorted(self.data[d].events, key=lambda event: "-important-" in event.tags, reverse=True)
        if not len(self.data):
            return "Empty, add tasks todo!"
        if day is None:
            dlistviews = [self.data[date].listView(tag=tag) if pointer is None else self.data[date].listView(pointedEvent=pointer - sum(self.numOfEvents[:idx]), tag=tag) for idx, date in enumerate(self.data) if date >= TODAY or pointer is not None]
            return "\n".join(d for d in dlistviews if d.split('\n')[1] != "") if any(d.split('\n')[1] != "" for d in dlistviews) else f"No tasks with tag {tag}"
        else:
            tagsDay = []
            for e in self.data[day].events:
                tagsDay.extend(e.tags)
            if tag in tagsDay or tag is None:
                return self.data[day].listView(pointedEvent=pointer, tag=tag)
            else:
                return f"No tasks with tag {tag}"
    def detailedView(self, day=None, tag=None, hideDone=False):
        for d in self.data: self.data[d].events = sorted(self.data[d].events, key=lambda event: "-important-" in event.tags, reverse=True)
        if not len(self.data):
            return "Empty, add tasks todo!"
        if day is None:
            dlistviews = [self.data[date].detailedView(tag=tag, hideDone=hideDone) for date in self.data if date >= TODAY]
            return "\n\n".join(d for d in dlistviews if d.split('\n')[1] != "") if any(d.split('\n')[1] != "" for d in dlistviews) else (f"No tasks with tag {tag}" if tag is not None else "No tasks todo!")
        else:
            tagsDay = []
            doneAll = True
            for e in self.data[day].events:
                tagsDay.extend(e.tags)
                doneAll = doneAll and e.status
            if (tag in tagsDay or tag is None) and not (hideDone and doneAll):
                return self.data[day].detailedView(tag=tag, hideDone=hideDone)
            else:
                if hideDone and doneAll:
                    return f"All tasks TODAY done!!!"
                else:
                    return f"No tasks with tag {tag}"
    def calendarView(self, dateString, tag=None, showAll=True):
            for day in self.data: self.data[day].events = sorted(self.data[day].events, key=lambda event: "-important-" in event.tags, reverse=True)
            ## dd - placeholder for day
            ## [ ] ttttttttttt - placeholder for task
            allData = copy.deepcopy(self.data)
            if showAll:
                with open(CONFIG["archivePath"], "r") as f:
                    archieved = {date:Day(date, day) for date, day in json.load(f).items()}
                for date in archieved:
                    allData[date] = archieved[date]
            outputLength = self.outputLength
            ntask = self.ntask
            year, month = map(int, dateString.split("-"))
            monthLength = [31, 28 + (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            monthName = monthNames[month - 1]
            firstDay = (datetime.date(year, month, 1).weekday()+1)%7
            ncells = (firstDay + monthLength[month-1])
            nrows = ncells // 7 + (ncells % 7 != 0)
            ncells = nrows * 7
            separator = "─"*(outputLength+2)
            firstLineS = lambda weekday: "  dd"+" "*((outputLength-5)//2-2)+weekday+" "*(outputLength-5-((outputLength-5)//2-2))
            followLineS = f"  dd{' '*(outputLength-3)} "
            taskPlaceholder = f"[ ] {'t'*(outputLength-4)}"
            taskPlaceholderl = f"│ {taskPlaceholder} | {taskPlaceholder} | {taskPlaceholder} | {taskPlaceholder} | {taskPlaceholder} | {taskPlaceholder} | {taskPlaceholder} |\n"*ntask
            calendarTemplate = f"{dateString} {monthName}                                                                                                           \n┌{separator}┬{separator}┬{separator}┬{separator}┬{separator}┬{separator}┬{separator}┐\n│{firstLineS('Sun')}│{firstLineS('Mon')}│{firstLineS('Tue')}│{firstLineS('Wed')}│{firstLineS('Thu')}│{firstLineS('Fri')}│{firstLineS('Sat')}│\n"
            for _ in range(nrows-1):
                calendarTemplate += f"{taskPlaceholderl}├{separator}┼{separator}┼{separator}┼{separator}┼{separator}┼{separator}┼{separator}┤\n│{followLineS}|{followLineS}|{followLineS}|{followLineS}|{followLineS}|{followLineS}|{followLineS}|\n"
            calendarTemplate += f"{taskPlaceholderl}└{separator}┴{separator}┴{separator}┴{separator}┴{separator}┴{separator}┴{separator}┘\n"
            for _ in range(firstDay):
                calendarTemplate = calendarTemplate.replace(f"dd", "  ", 1)
            for date in range(1, monthLength[month-1]+1):
                calendarTemplate = calendarTemplate.replace(f"dd", f"{date}{' '*int(date<10)}", 1)
            for _ in range(ncells-firstDay-monthLength[month-1]):
                calendarTemplate = calendarTemplate.replace(f"dd", "  ", 1)
            taskList = [[] for _ in range(firstDay)] + [(allData[f"{dateString}-{'0'*int(date<10)}{date}"].calendarView(outputLength=outputLength, tag=tag) if f"{dateString}-{'0'*int(date<10)}{date}" in allData else []) for date in range(1, monthLength[month-1]+1)] + [[] for _ in range(ncells-firstDay-monthLength[month-1])]
            for i, t in enumerate(taskList):
                if len(t) < ntask: t += [" "*outputLength]*(ntask-len(t))
                taskList[i] = t[:ntask]
            for week in range(nrows):
                weekList = taskList[week*7:(week+1)*7]
                weekList = [task for sublist in zip(*weekList) for task in sublist]
                for task in weekList:
                    calendarTemplate = calendarTemplate.replace(taskPlaceholder, task, 1)
            print(calendarTemplate)
            return calendarTemplate

"""
Calendar Template:
2024-02 February
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│       Sun       │       Mon       │       Tue       │       Wed       │  1    Thu       │  2    Fri       │  3    Sat       │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│  4              │  5              │  6              │  7              │  8              │  9              │  10             │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│  11             │  12             │  13             │  14             │  15             │  16             │  17             │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│  18             │  19             │  20             │  21             │  22             │  23             │  24             │
│                 │                 │                 │                 │ [X] CIM Webpage │                 │                 │
│                 │                 │                 │                 │ [ ] STAT2602... │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│  25             │  26             │  27             │  28             │  29             │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
│                 │                 │                 │                 │                 │                 │                 │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┘
"""
