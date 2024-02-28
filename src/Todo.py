import os
import json
import copy
import datetime

from Day import Day
from config import CONFIG
from utils import getTODAY

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
                archived = {date:Day(date, day) for date, day in json.load(f).items()}
                for date in self.data:
                    if date < getTODAY():
                        archived[date] = copy.deepcopy(self.data[date])
        else:
            archived = {date: copy.deepcopy(self.data[date]) for date in self.data if date < getTODAY()}
        self.archived = archived
        self.autoArchive()
    def autoArchive(self):
        if any(date < getTODAY() for date in self.data):
            for date in self.data:
                if date < getTODAY():
                    self.archived[date] = copy.deepcopy(self.data[date])
            self.data = {date: self.data[date] for date in self.data if date >= getTODAY()}
        if CONFIG["autoAddUncompletedTasks"]:
            for date in self.archived:
                if date < getTODAY():
                    for event in self.archived[date].events:
                        if not event.status and "-done-" not in event.tags:
                            jsonifiedEvent = copy.deepcopy(event.jsonify())
                            jsonifiedEvent["tags"].insert(0, "-overdue-")
                            jsonifiedEventDone = copy.deepcopy(jsonifiedEvent)
                            jsonifiedEventDone["status"] = True
                            if not (getTODAY() in self.data and (jsonifiedEvent in self.data[getTODAY()].jsonify()["events"] or jsonifiedEventDone in self.data[getTODAY()].jsonify()["events"])):
                                self.addEvent(getTODAY(), jsonifiedEvent)
                            elif not (getTODAY() in self.data and jsonifiedEvent in self.data[getTODAY()].jsonify()["events"]):
                                event.tags.append("-done-")
    def saveArchive(self):
        with open(CONFIG["archivePath"], "w") as f:
            json.dump({date:self.archived[date].jsonify() for date in self.archived}, f)
    def save(self):
        self.autoArchive()
        self.saveArchive()
        with open(CONFIG["dataPath"], "w") as f:
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
        self.save()
    def deleteEvent(self, dateString, eventIndex):
        try: 
            self.data[dateString].deletEvent(eventIndex)
            if len(self.data[dateString].events) == 0:
                self.data.pop(dateString)
        except:
            print("Invalid Date or Index")
        self.numOfEvents = [len(self.data[date].events) for date in self.data]
        self.save()
    def listView(self, day=None, pointer=None, tag=None):
        self.save()
        for d in self.data: self.data[d].events = sorted(self.data[d].events, key=lambda event: "-important-" in event.tags, reverse=True)
        if not len(self.data) and day is None:
            return "Empty, add tasks todo!"
        if day is None:
            dlistviews = [self.data[date].listView(tag=tag) if pointer is None else self.data[date].listView(pointedEvent=pointer - sum(self.numOfEvents[:idx]), tag=tag) for idx, date in enumerate(self.data) if date >= getTODAY() or pointer is not None]
            return "\n".join(d for d in dlistviews if d.split('\n')[1] != "") if any(d.split('\n')[1] != "" for d in dlistviews) else f"No tasks with tag {tag}"
        else:
            if day not in self.data and day not in self.archived:
                return f"No tasks on {day}"
            if day in self.data:
                data = self.data
            else:
                data = self.archived
            tagsDay = []
            for e in data[day].events:
                tagsDay.extend(e.tags)
            if tag in tagsDay or tag is None:
                return data[day].listView(pointedEvent=pointer, tag=tag)
            else:
                return f"No tasks with tag {tag}"
    def detailedView(self, day=None, tag=None, hideDone=False):
        self.save()
        for d in self.data: self.data[d].events = sorted(self.data[d].events, key=lambda event: "-important-" in event.tags, reverse=True)
        if not len(self.data) and day is None:
            return "Empty, add tasks todo!"
        if day is None:
            dlistviews = [self.data[date].detailedView(tag=tag, hideDone=hideDone) for date in self.data if date >= getTODAY()]
            return "\n\n".join(d for d in dlistviews if d.split('\n')[1] != "") if any(d.split('\n')[1] != "" for d in dlistviews) else (f"No tasks with tag {tag}" if tag is not None else "No tasks todo!")
        else:
            if day not in self.data and day not in self.archived:
                return f"No tasks on {day}"
            if day in self.data:
                data = self.data
            else:
                data = self.archived
            tagsDay = []
            doneAll = True
            for e in data[day].events:
                tagsDay.extend(e.tags)
                doneAll = doneAll and e.status
            if (tag in tagsDay or tag is None) and not (hideDone and doneAll):
                return data[day].detailedView(tag=tag, hideDone=hideDone)
            else:
                if hideDone and doneAll:
                    return f"All tasks today done!!!"
                else:
                    return f"No tasks with tag {tag}"
    def calendarView(self, dateString, tag=None, showAll=True):
            for day in self.data: self.data[day].events = sorted(self.data[day].events, key=lambda event: "-important-" in event.tags, reverse=True)
            ## dd - placeholder for day
            ## [ ] ttttttttttt - placeholder for task
            allData = copy.deepcopy(self.data)
            if showAll:
                with open(CONFIG["archivePath"], "r") as f:
                    archived = {date:Day(date, day) for date, day in json.load(f).items()}
                for date in archived:
                    allData[date] = archived[date]
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
            taskPlaceholderl = f"│ {taskPlaceholder} │ {taskPlaceholder} │ {taskPlaceholder} │ {taskPlaceholder} │ {taskPlaceholder} │ {taskPlaceholder} │ {taskPlaceholder} │\n"*ntask
            calendarTemplate = f"{dateString} {monthName}                                                                                                           \n┌{separator}┬{separator}┬{separator}┬{separator}┬{separator}┬{separator}┬{separator}┐\n│{firstLineS('Sun')}│{firstLineS('Mon')}│{firstLineS('Tue')}│{firstLineS('Wed')}│{firstLineS('Thu')}│{firstLineS('Fri')}│{firstLineS('Sat')}│\n"
            for _ in range(nrows-1):
                calendarTemplate += f"{taskPlaceholderl}├{separator}┼{separator}┼{separator}┼{separator}┼{separator}┼{separator}┼{separator}┤\n│{followLineS}│{followLineS}│{followLineS}│{followLineS}│{followLineS}│{followLineS}│{followLineS}│\n"
            calendarTemplate += f"{taskPlaceholderl}└{separator}┴{separator}┴{separator}┴{separator}┴{separator}┴{separator}┴{separator}┘\n"
            for _ in range(firstDay):
                calendarTemplate = calendarTemplate.replace(f"dd", "  ", 1)
            for date in range(1, monthLength[month-1]+1):
                calendarTemplate = calendarTemplate.replace(f"dd", f"{date}{' '*int(date<10)}", 1)
            for _ in range(ncells-firstDay-monthLength[month-1]):
                calendarTemplate = calendarTemplate.replace(f"dd", "  ", 1)
            taskList = [[] for _ in range(firstDay)] + [(allData[f"{dateString}-{'0'*int(date<10)}{date}"].calendarView(outputLength=outputLength, tag=tag) if f"{dateString}-{'0'*int(date<10)}{date}" in allData else []) for date in range(1, monthLength[month-1]+1)] + [[] for _ in range(ncells-firstDay-monthLength[month-1])]
            for i, t in enumerate(taskList):
                if len(t) <= ntask: t += [" "*outputLength]*(ntask-len(t))
                else: taskList[i] = t[:ntask-1] + ["..."+" "*(outputLength-3)]
            for week in range(nrows):
                weekList = taskList[week*7:(week+1)*7]
                weekList = [task for sublist in zip(*weekList) for task in sublist]
                for task in weekList:
                    calendarTemplate = calendarTemplate.replace(taskPlaceholder, task, 1)
            return calendarTemplate

