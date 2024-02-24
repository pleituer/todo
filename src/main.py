import os
import datetime
import sys
import re
import json

from Todo import Todo
from Event import Event
from config import CONFIG, CONFIG_NAME
from utils import hexToRGBString, tagColorWrap, TODAY
from Input import Input, UP, DOWN, LEFT, RIGHT, ENTER, INVALID

dateRegex = r"^\d{4}"+CONFIG["dateSeperator"]+r"\d{2}"+CONFIG["dateSeperator"]+r"\d{2}$"
dateRegex2 = r"^\d{4}"+CONFIG["dateSeperator"]+r"\d{2}$"

config_str = "\n".join([f"    - {key}: {CONFIG[key]}" for key in CONFIG])

HELP_TEXT = f"""command: todo [OPTIONS] <ARGUMENTS>

A todo list coded in python. Without any options specified, enters interactive mode.

CONFIGURATION:
    Date format: YYYY{CONFIG['dateSeperator']}MM{CONFIG['dateSeperator']}DD
    See config.json for configuration options.
    Current configuration:
{config_str}

OPTIONS & ARGUMENTS:
    -h  --help                  display this help text
        --examples <mode>       display examples
                                modes: cli, interactive
        --tagList               display all tags (with their colors)
    -a  --add                   add an event (see dateRegex for day format)
    -d  --delete                delete an event
        --delete <day>          delete an event of a specific day
    -l  --list                  list all events
        --list <day>            list events for a specific day (see dateRegex for day format)
    -d  --detailed              list all events with details
        --detailed <day>        list events for a specific day with details (see dateRegex for day format)
    -c  --calendar              display calendar view
        --calendar <date>       display calendar view for a specific date (see dateRegex2 for date format)
        -tag <tag>              list events with a specific tag
                                Can be applied on top of -l, --list, -ld, --listdetailed, -c, and --calendar
    -t  --today                 list today's events in detailed view, completed task are hidden
        --today -showAll        shows all tasks of today, including completed tasks
    -e  --edit                  edit an event
        --edit <day>            edit an event of a specific day
    -f  --done                  mark an event as done
        --done <day>            mark an event of a specific day as done
    -uf --undone                mark an event as undone
        --undone <day>          mark an event of a specific day as undone
    -i  --important             add an important tag to an event
        --config <key> <value>  change configuration
    
SPECIAL TAGS:
    -important-    A task with this tag will be put on higher piority
    -overdue-      A task will be marked overdue if it has no been done by the end of the day
    -done-         A task will be marked done
    -undone-       A task will be marked undone"""

EXAMPLES_CLI = """EXAMPLES (Command Line):

~$ todo -a 
Day: 2024-01-01
Task: New Year's Day
Description: Celebrate the new year
Tags: holiday, party
Task added successfully

~$ todo -l
==== 2024-01-01 ====
  [ ] New Year's Day
=====================

~$ todo -a
Day: 2024-02-14
Task: Valentine's Day
Description: Celebrate love
Tags: holiday

~$ todo -listdetailed "2024-02-14"
==== 2024-02-14 ====
Task: Valentine's Day
Description: Celebrate love
Tags: holiday
Done: No
=====================

~$ todo -f
Select day:
==== 2024-01-01 ====
    [ ] New Year's Day
=====================
==== 2024-02-14 ====
    [ ] Valentine's Day <-
=====================
Selected day: 2024-02-14
Confirm (y/n): y
Task marked as done

~$ todo -l
==== 2024-01-01 ====
    [ ] New Year's Day
=====================
==== 2024-02-14 ====
    [X] Valentine's Day
====================="""

def checkValidFormat(dateString, regex=dateRegex):
    if not re.match(regex, dateString):
        print("Invalid date format")
        exit()
    elif int(dateString.split(CONFIG["dateSeperator"])[1]) > 12 or (len(dateString.split(CONFIG["dateSeperator"])) > 2 and int(dateString.split(CONFIG["dateSeperator"])[2]) > 31):
        print("Invalid date")
        exit()

def selectTask(todo):
    kb = Input()
    todoList = todo.listView(pointer=0).split("\n")
    refreshText = f"\x1b[{len(todoList)+1}A"
    pointedTask = 0
    print("Press 'q' to exit\nPress ENTER to select\n\nPress UP/DOWN to navigate\n\n")
    print(todo.listView(pointer=pointedTask))
    ch = ''
    if len(todo.numOfEvents) == 0:
        print("No tasks to select")
        exit()
    while True:
        print(refreshText)
        print(todo.listView(pointer=pointedTask))
        ch = kb.getch()
        if ch == UP or ch == "w" or ch == "W":
            pointedTask = max(0, pointedTask - 1)
        elif ch == DOWN or ch == "s" or ch == "S":
            pointedTask = min(sum(todo.numOfEvents) - 1, pointedTask + 1)
        elif ch == ENTER:
            break
        elif ch == 'q':
            print('Exited')
            exit()
    day = None
    for date in todo.data:
        if pointedTask < len(todo.data[date].events):
            day = date
            break
        pointedTask -= len(todo.data[date].events)
    return day, pointedTask

def calendarWarn():
    kb = Input(t=0.1, showCursor=True)
    print("WARNING: Terminal size too small to display calendar view")
    print("Please resize terminal")
    print("Or press ENTER to continue in calendar view (WARNING: may not be displayed properly)")
    ch = ''
    while ch != ENTER and os.get_terminal_size().columns <= 8+7*(2+int(CONFIG["outputLength"])):
        ch = kb.getch()
    print("\x1b[4A")

def clearPastTasks(todo):
    today = TODAY
    for day in todo.data.keys():
        events = todo.data[day].events
        if day < today:
            todo.data[day].events = [event for event in events if event.status == False]
    todo.data = {day: todo.data[day] for day in todo.data.keys() if len(todo.data[day].events)}

def configCheck():
    if "-important-" not in CONFIG["tagColors"] or "-overdue-" not in CONFIG["tagColors"] or "-done-" not in CONFIG["tagColors"] or "-undone-" not in CONFIG["tagColors"]:
        CONFIG["tagColors"]["-important-"] = "#FF0000"
        CONFIG["tagColors"]["-overdue-"] = "#FFA07A"
        CONFIG["tagColors"]["-done-"] = "#21f141"
        CONFIG["tagColors"]["-undone-"] = ""
        with open(os.path.join(os.environ["todoPath"], CONFIG_NAME), "w") as f:
            f.write(json.dumps(CONFIG, indent=4))
    if "todoPath" not in os.environ:
        os.environ["todoPath"] = os.path.dirname(__file__)
    if not os.path.exists(CONFIG["dataPath"]):
        CONFIG["dataPath"] = os.path.join(os.environ["todoPath"], "data.json")
        with open(os.path.join(os.environ["todoPath"], CONFIG_NAME), "w") as f:
            f.write(json.dumps(CONFIG, indent=4))

def _help(todo):
    print(HELP_TEXT)
def _example(todo):
    if len(sys.argv) == 3:
        if sys.argv[2].lower() == "cli":
            print(EXAMPLES_CLI)
        elif sys.argv[2].lower() == "interactive":
            print("No examples available for interactive mode yet")
        else:
            print("Invalid Mode")
    else:
        print("ERROR: Mode not specified")
def _add(todo):
    print("Adding task, type '\quit' to exit")
    inputs = []
    for prompt in ["Day (YYYY-MM-DD): ", "Task: ", "Description: ", "Tags: "]:
        inp = input(prompt).strip()
        if inp == "\\quit":
            print("Exited")
            exit()
        if prompt == "Day (YYYY-MM-DD): ":
            checkValidFormat(inp)
            today = TODAY
            if inp < today:
                print("Cannot add task for past date")
                exit()
        inputs.append(inp)
    dateString = inputs[0]
    dataDict = {
        "title": inputs[1],
        "description": inputs[2],
        "tags": inputs[3].split(", "),
        "status": False
    }
    todo.addEvent(dateString, dataDict)
    print("Task added successfully")
def _delete(todo):
    print("Deleting task")
    if len(sys.argv) == 2:
        day, pointedTask = selectTask(todo)
    elif len(sys.argv) == 3:
        day = sys.argv[2]
        checkValidFormat(day)
        if day not in todo.data.keys():
            print("No tasks for this day")
            exit()
        tempTodo = Todo()
        tempTodo.data = {day: todo.data[day]}
        tempTodo.numOfEvents = [len(todo.data[day].events)]
        day, pointedTask = selectTask(tempTodo)
    else:
        print("Invalid Command/Format")
        exit()
    if input("Confirm (y/n): ").strip().lower() == "y":
        todo.deleteEvent(day, pointedTask)
        print("Task deleted successfully")
def _list(todo):
    if len(sys.argv) == 2:
        print(todo.listView())
    elif len(sys.argv) == 3:
        checkValidFormat(sys.argv[2])
        if sys.argv[2] not in todo.data.keys():
            print("No tasks for this day")
        else:
            print(todo.listView(day=sys.argv[2]))
    elif len(sys.argv) == 4 and sys.argv[2] != "-tag":
        print("Invalid Command/Format")
        exit()
    elif len(sys.argv) == 4 and sys.argv[2] == "-tag":
        tag = sys.argv[3]
        print(todo.listView(tag=tag))
    elif len(sys.argv) == 5:
        if sys.argv[3] != "-tag" and sys.argv[2] != "-tag":
            print("Invalid Command/Format")
            exit()
        tag = sys.argv[4] if sys.argv[3] == "-tag" else sys.argv[3]
        day = sys.argv[2] if sys.argv[3] == "-tag" else sys.argv[4]
        checkValidFormat(day)
        print(todo.listView(day=day, tag=tag))
    else:
        print("Invalid Command/Format")
        exit()
def _listdetailed(todo):
    if len(sys.argv) == 2:
        print(todo.detailedView())
    elif len(sys.argv) == 3:
        checkValidFormat(sys.argv[2])
        if sys.argv[2] not in todo.data.keys():
            print("No tasks for this day")
        else:
            print(todo.detailedView(day=sys.argv[2]))
    elif len(sys.argv) == 4 and sys.argv[2] != "-tag":
        print("Invalid Command/Format")
        exit()
    elif len(sys.argv) == 4 and sys.argv[2] == "-tag":
        tag = sys.argv[3]
        print(todo.detailedView(tag=tag))
    elif len(sys.argv) == 5:
        if sys.argv[3] != "-tag" and sys.argv[2] != "-tag":
            print("Invalid Command/Format")
            exit()
        tag = sys.argv[4] if sys.argv[3] == "-tag" else sys.argv[3]
        day = sys.argv[2] if sys.argv[3] == "-tag" else sys.argv[4]
        checkValidFormat(day)
        print(todo.detailedView(day=day, tag=tag))
    else:
        print("Invalid Command/Format")
        exit()
def _today(todo):
    today = TODAY
    if len(sys.argv) == 2:
        if today not in todo.data.keys():
            print("No tasks for today")
        else:
            print(todo.detailedView(day=today, hideDone=True))
    elif len(sys.argv) == 3 and sys.argv[2] == "-showAll":
        if today not in todo.data.keys():
            print("No tasks for today")
        else:
            print(todo.detailedView(day=today, hideDone=False))
    else:
        print("Invalid Command/Format")
        exit()
def _edit(todo):
    print("Editing task")
    pointedTask = None
    if len(sys.argv) == 2:
        day, pointedTask = selectTask(todo)
    elif len(sys.argv) == 3:
        day = sys.argv[2]
        checkValidFormat(day)
        if day not in todo.data.keys():
            print("No tasks for this day")
            exit()
        tempTodo = Todo()
        tempTodo.data = {day: todo.data[day]}
        tempTodo.numOfEvents = [len(todo.data[day].events)]
        day, pointedTask = selectTask(tempTodo)
    else:
        print("Invalid Command/Format")
        exit()
    print("Original task details: ")
    print(todo.data[day].events[pointedTask].detailedView())
    print()
    print("Enter \\none if you don't want to edit that field, type '\\quit' to exit")
    inputs = []
    for prompt in ["Task: ", "Description: ", "Tags: "]:
        inp = input(prompt).strip()
        if inp == "\\quit":
            print("Exited")
            exit()
        inputs.append(inp)
    dataDict = {
        "title": inputs[0] if inputs[0] != "\\none" else todo.data[day].events[pointedTask].title,
        "description": inputs[1] if inputs[1] != "\\none" else todo.data[day].events[pointedTask].description,
        "tags": inputs[2].split(", ") if inputs[2] != "\\none" else todo.data[day].events[pointedTask].tags,
        "status": todo.data[day].events[pointedTask].status
    }
    todo.data[day].events[pointedTask] = Event(dataDict)
    print("Task edited successfully")
def _done(todo):
    print("Marking task done")
    pointedTask = None
    if len(sys.argv) == 2:
        day, pointedTask = selectTask(todo)
    elif len(sys.argv) == 3:
        day = sys.argv[2]
        checkValidFormat(day)
        if day not in todo.data.keys():
            print("No tasks for this day")
            exit()
        tempTodo = Todo()
        tempTodo.data = {day: todo.data[day]}
        tempTodo.numOfEvents = [len(todo.data[day].events)]
        day, pointedTask = selectTask(tempTodo)
    else:
        print("Invalid Command/Format")
        exit()
    todo.data[day].events[pointedTask].done()
    print("Task marked done successfully")
def _undone(todo):
    print("Marking task undone")
    if len(sys.argv) == 2:
        day, pointedTask = selectTask(todo)
    elif len(sys.argv) == 3:
        day = sys.argv[2]
        checkValidFormat(day)
        if day not in todo.data.keys():
            print("No tasks for this day")
            exit()
        tempTodo = Todo()
        tempTodo.data = {day: todo.data[day]}
        tempTodo.numOfEvents = [len(todo.data[day].events)]
        day, pointedTask = selectTask(tempTodo)
    else:
        print("Invalid Command/Format")
        exit()
    todo.data[day].events[pointedTask].undone()
    print("Task marked undone successfully")
def _calendar(todo):
    print("Calendar View")
    calendarWarn()
    print("\x1b[0m", end="")
    if len(sys.argv) == 2:
        print(todo.calendarView(dateString=datetime.datetime.now().strftime("%Y-%m")))
    elif len(sys.argv) == 3: 
        dateString = sys.argv[2]
        checkValidFormat(dateString, regex=dateRegex2)
        print(todo.calendarView(dateString=dateString))
    elif len(sys.argv) == 4 and sys.argv[2] != "-tag":
        print("Invalid Command/Format")
        exit()
    elif len(sys.argv) == 4 and sys.argv[2] == "-tag":
        tag = sys.argv[3]
        print(todo.calendarView(dateString=datetime.datetime.now().strftime("%Y-%m"), tag=tag))
    elif len(sys.argv) == 5:
        if sys.argv[3] != "-tag" and sys.argv[2] != "-tag":
            print("Invalid Command/Format")
            exit()
        tag = sys.argv[4] if sys.argv[3] == "-tag" else sys.argv[3]
        dateString = sys.argv[2] if sys.argv[3] == "-tag" else sys.argv[4]
        checkValidFormat(dateString, regex=CONFIG["dateRegex2"])
        print(todo.calendarView(dateString=dateString, tag=tag))
    else:
        print("Invalid Command/Format")
        exit()
def _config(todo):
    if len(sys.argv) == 4:
        key = sys.argv[2]
        value = sys.argv[3]
        if key in CONFIG.keys():
            oldvalue = CONFIG[key]
            if input(f"Change value of {key}, {oldvalue} -> {value}? (y/n): ").strip().lower() != "y":
                print("Exited")
                exit()
            CONFIG[key] = value
            with open(os.environ["todo_configPath"], "w") as f:
                f.write(json.dumps(CONFIG, indent=4))
            print(f"Configuration changed value of {key}, {oldvalue} -> {value}")
        else:
            print("Invalid configuration key")
    else:
        print("Invalid Command/Format")
        exit()
def _important(todo):
    print("Adding important tag to task")
    if len(sys.argv) == 2:
        day, pointedTask = selectTask(todo)
    elif len(sys.argv) == 3:
        day = sys.argv[2]
        checkValidFormat(day)
        if day not in todo.data.keys():
            print("No tasks for this day")
            exit()
        tempTodo = Todo()
        tempTodo.data = {day: todo.data[day]}
        tempTodo.numOfEvents = [len(todo.data[day].events)]
        day, pointedTask = selectTask(tempTodo)
    else:
        print("Invalid Command/Format")
        exit()
    todo.data[day].events[pointedTask].tags.insert(0, "-important-")
    print("Important tag added successfully")
def _taglist(todo): 
    print("Special Tags")
    print(f"""important: {hexToRGBString(CONFIG["tagColors"]["-important-"])}{CONFIG["important"]}\x1b[0m
overdue: {hexToRGBString(CONFIG["tagColors"]["-overdue-"])}{"-overdue-"}\x1b[0m
done: {hexToRGBString(CONFIG["tagColors"]["-done-"])}{f"[{CONFIG['done']}]"}\x1b[0m
undone: {hexToRGBString(CONFIG["tagColors"]["-undone-"])}{f"[ ]"}\x1b[0m
""")
    print("Custom Tags")
    tagList = [tag for tag in CONFIG["tagColors"].keys() if tag not in ["-important-", "-overdue-", "-done-", "-undone-"]]
    for date in todo.data:
        for event in todo.data[date].events:
            for tag in event.tags:
                if tag not in tagList:
                    tagList.append(tag)
    for tag in tagList:
        print(f"  ◇ {tagColorWrap(tag)}\x1b[0m")

def main():
    configCheck()
    todo = Todo(CONFIG["dataPath"]) if os.path.exists(CONFIG["dataPath"]) else Todo()
    if CONFIG["autoClearCompletedPastTasks"]:
        clearPastTasks(todo)
    if len(sys.argv) == 1:
        print("Entering Interactive Mode")
        print("ERROR: Interactive Mode not available yet")
        print("Pay up 69 bitcoins to speed up development by 1 day")
    else:
        if sys.argv[1] in ["-h", "--help", "help"]: _help(todo)
        elif sys.argv[1] in ["--examples", "examples"]: _example(todo)
        elif sys.argv[1] in ["--tagList", "tagList"]: _taglist(todo)
        elif sys.argv[1] in ["-a", "--add", "add"]: _add(todo)
        elif sys.argv[1] in ["-d", "--delete", "delete"]: _delete(todo)
        elif sys.argv[1] in ["-l", "--list", "list"]:  _list(todo)
        elif sys.argv[1] in ["-d", "--detailed", "detailed"]: _listdetailed(todo)
        elif sys.argv[1] in ["-t", "--today", "today"]: _today(todo)
        elif sys.argv[1] in ["-e", "--edit", "edit"]: _edit(todo)
        elif sys.argv[1] in ["-f", "--done", "done"]: _done(todo)            
        elif sys.argv[1] in ["-uf", "--undone", "undone"]: _undone(todo)
        elif sys.argv[1] in ["-c", "--calendar", "calendar"]: _calendar(todo)
        elif sys.argv[1] in ["--config", "config"]: _config(todo)
        elif sys.argv[1] in ["-i", "--important", "important"]: _important(todo)
        else: print("Invalid Command/Format")
        todo.save(CONFIG["dataPath"])

if __name__ == "__main__":
    main()