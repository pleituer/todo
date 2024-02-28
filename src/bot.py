import os
import sys
import pytz
from datetime import datetime
from typing import Callable
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord import app_commands

from Todo import Todo
from config import CONFIG
from utils import checkValidFormat, getTODAY, dateRegex, dateRegex2

load_dotenv()

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(client=bot)

serverID = os.getenv("SERVER_ID")
server = discord.Object(id=int(serverID))

todo = Todo(CONFIG["dataPath"])
sudoers = [int(s) for s in CONFIG["sudoers"]]

LOGGER_PATH = "D:/Peter/Programming//todolist/logs"
errLOGGER_PATH = "D:/Peter/Programming/todolist/errlogs"

ERROR_COLOR = 0xff0000
WARNING_COLOR = 0xffff00
BOT_COLOR = 0x87cefa

UTC8 = pytz.timezone('Etc/GMT-8')

def logCommand(user, commandName, **kwargs):
    if os.path.exists(os.path.join(LOGGER_PATH, getTODAY()+".log")): mode = "a"
    else: mode = "w"
    with open(os.path.join(LOGGER_PATH, getTODAY()+".log"), mode) as f:
        f.write(f"{datetime.now(tz=UTC8)} - {user} executed command: {commandName} - arguments: {kwargs}\n")
    print(f"{datetime.now(tz=UTC8)} - {user} executed command: {commandName} - arguments: {kwargs}")

def logMsg(msg):
    if os.path.exists(os.path.join(LOGGER_PATH, getTODAY()+".log")): mode = "a"
    else: mode = "w"
    with open(os.path.join(LOGGER_PATH, getTODAY()+".log"), mode) as f:
        f.write(f"{datetime.now(tz=UTC8)}: {msg}\n")
    print(f"{datetime.now(tz=UTC8)}: {msg}")

def logErr(err):
    if os.path.exists(os.path.join(errLOGGER_PATH, getTODAY()+".log")): mode = "a"
    else: mode = "w"
    with open(os.path.join(errLOGGER_PATH, getTODAY()+".log"), mode) as f:
        f.write(f"{datetime.now(tz=UTC8)}: {err}\n")
    print(f"{datetime.now(tz=UTC8)}: {err}")

def Embed(interaction, *args, **kwargs):
    embed = discord.Embed(*args, **kwargs)
    embed.set_author(name="dodo", icon_url=interaction.user.avatar.url )
    embed.set_thumbnail(url=bot.user.avatar.url)
    return embed

def errorMsg(interaction, msg, type="error"):
    type2Tits = {"error": "Error", "warning": "Warning"}
    logErr(f"{datetime.now(tz=UTC8)}: {type2Tits[type]} - {interaction.user} - {msg}")
    embed = Embed(interaction, title=type2Tits[type], description=msg, color=(ERROR_COLOR if type=="error" else WARNING_COLOR))
    return embed

def deleteOnView(self, embed):
    embed.clear_fields()
    embed.add_field(name="Selected", value=self.todo.data[self.selected[0]].events[self.selected[1]].detailedView(col=False), inline=False)
    embed.add_field(name="Confirmation", value="Confirm delete Task?", inline=False)
def markdoneOnView(self, embed):
    embed.clear_fields()
    task = self.todo.data[self.selected[0]].events[self.selected[1]]
    task.done()
    self.todo.save()
    embed.add_field(name="Marked task", value=task.detailedView(col=False), inline=False)
def markundoneOnView(self, embed):
    embed.clear_fields()
    task = self.todo.data[self.selected[0]].events[self.selected[1]]
    task.undone()
    self.todo.save()
    embed.add_field(name="Marked task", value=task.detailedView(col=False), inline=False)
def markimportantOnView(self, embed):
    embed.clear_fields()
    task = self.todo.data[self.selected[0]].events[self.selected[1]]
    task.tags.insert(0, "-important-")
    self.todo.save()
    embed.add_field(name="Marked task", value=task.detailedView(col=False), inline=False)

class SelectView(discord.ui.View):
    def __init__(self, todo: Todo, nextView: discord.ui.View, onView: Callable[[discord.ui.View, discord.Embed], None], day: str = "-"):
        super().__init__()
        self.todo = todo
        self.nextView = nextView
        self.day = day
        self.onView = onView
        self.pointer = 0
        self.children[0].disabled = True
        self.selected = None
        dayIdx = list(self.todo.data.keys()).index(self.day) if self.day in self.todo.data else -1
        print(day)
        self.numOfEvents = [numOfEvent if idx == dayIdx else 0 for idx, numOfEvent in enumerate(self.todo.numOfEvents)]
        if self.pointer == sum(self.numOfEvents)-1: self.children[1].disabled = True
        logMsg(f"<SelectView>.Pointer -> {self.pointer}")

    @discord.ui.button(label="Prev", custom_id="prev", style=discord.ButtonStyle.blurple)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        self.pointer -= 1
        if self.pointer == 0: self.children[0].disabled = True
        self.children[1].disabled = False
        embed.clear_fields()
        for idx, day in enumerate(self.todo.data.values()):
            if day.date == self.day or self.day == "-":
                eventStr = "\n".join(day.listView(pointedEvent=self.pointer-sum(self.numOfEvents[:idx]), col=False).split("\n")[1:-1])
                embed.add_field(name=day.date, value=eventStr, inline=False)
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.defer()
        logMsg(f"<SelectView>.Pointer -> {self.pointer}")

    @discord.ui.button(label="Next", custom_id="next", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        self.pointer += 1
        self.children[0].disabled = False
        if self.pointer == sum(self.numOfEvents)-1: self.children[1].disabled = True
        print(self.pointer, self.numOfEvents)
        embed.clear_fields()
        for idx, day in enumerate(self.todo.data.values()):
            if day.date == self.day or self.day == "-":
                eventStr = "\n".join(day.listView(pointedEvent=self.pointer-sum(self.numOfEvents[:idx]), col=False).split("\n")[1:-1])
                embed.add_field(name=day.date, value=eventStr, inline=False)
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.defer()
        logMsg(f"<SelectView>.Pointer -> {self.pointer}")

    @discord.ui.button(label="Select", custom_id="select", style=discord.ButtonStyle.green)
    async def select(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        for idx, day in enumerate(self.todo.data.values()):
            if self.pointer+1 >= sum(self.numOfEvents[:idx]) and (day.date == self.day or self.day == "-"):
                self.selected = (day.date, self.pointer-sum(self.numOfEvents[:idx]))
        logMsg(f"<SelectView>.Selected -> {self.selected}")
        self.onView(self, embed)
        await interaction.message.edit(embed=embed, view=self.nextView(self.todo, self.selected, day = self.day))
        await interaction.response.defer()
        logMsg(f"<SelectView>.Selected -> {self.selected}")
class DeleteConfirmation(discord.ui.View):
    def __init__(self, todo: Todo, selected: tuple[str, int], **kwargs):
        super().__init__()
        self.todo = todo
        self.selected = selected
        self.kwargs = kwargs
        logMsg(f"<DeleteConfirmation>.Selected -> {self.selected}")
    
    @discord.ui.button(label="Confrim", custom_id="confirm", style=discord.ButtonStyle.red)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        day, idx = self.selected
        val = self.todo.data[self.selected[0]].events[self.selected[1]].detailedView(col=False)
        self.todo.deleteEvent(day, idx)
        self.children[0].disabled = True
        self.children[0].label = "Deleted"
        nembed = Embed(interaction, title="Task Deleted", description=f"Deleted a task in {day}", color=BOT_COLOR)
        nembed.add_field(name="Selected", value=val, inline=False)
        await interaction.message.edit(embed=nembed, view=self)
        await interaction.response.defer()
        logMsg(f"<DeleteConfirmation>.Confirmed -> {self.selected}")
        print([idx.label for idx in self.children])
    
    @discord.ui.button(label="Back", custom_id="back", style=discord.ButtonStyle.blurple)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        nembed = Embed(interaction, title="Deleting Task", description=f"proposed by {interaction.user}", color=BOT_COLOR)
        for idx, day in enumerate(self.todo.data.values()):
            eventStr = "\n".join(day.listView(pointedEvent=0-int(idx != 0), col=False).split("\n")[1:-1])
            nembed.add_field(name=day.date, value=eventStr, inline=False)
        await interaction.message.edit(embed=nembed, view=SelectView(self.todo, DeleteConfirmation, deleteOnView))
        await interaction.response.defer()
        logMsg(f"<DeleteConfirmation>.Back -> {self.selected}")
class DoneView(discord.ui.View):
    def __init__(self, todo: Todo, selected: tuple[str, int], **kwargs):
        super().__init__()
        self.todo = todo
        self.selected = selected
        self.kwargs = kwargs
    
    @discord.ui.button(label="Back", custom_id="back", style=discord.ButtonStyle.blurple)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        nembed = Embed(interaction, title="Marking Task Done", description=f"proposed by {interaction.user}", color=BOT_COLOR)
        for idx, day in enumerate(self.todo.data.values()):
            eventStr = "\n".join(day.listView(pointedEvent=0-int(idx != 0), col=False).split("\n")[1:-1])
            nembed.add_field(name=day.date, value=eventStr, inline=False)
        await interaction.message.edit(embed=nembed, view=SelectView(self.todo, DoneView, markdoneOnView))
        await interaction.response.defer()
        logMsg(f"<DoneView>.Back -> {self.selected}")
class unDoneView(discord.ui.View):
    def __init__(self, todo: Todo, selected: tuple[str, int], **kwargs):
        super().__init__()
        self.todo = todo
        self.selected = selected
        self.kwargs = kwargs
    
    @discord.ui.button(label="Back", custom_id="back", style=discord.ButtonStyle.blurple)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        nembed = Embed(interaction, title="Marking Task unDone", description=f"proposed by {interaction.user}", color=BOT_COLOR)
        for idx, day in enumerate(self.todo.data.values()):
            eventStr = "\n".join(day.listView(pointedEvent=0-int(idx != 0), col=False).split("\n")[1:-1])
            nembed.add_field(name=day.date, value=eventStr, inline=False)
        await interaction.message.edit(embed=nembed, view=SelectView(self.todo, DoneView, markundoneOnView))
        await interaction.response.defer()
        logMsg(f"<unDoneView>.Back -> {self.selected}")
class ImportantView(discord.ui.View):
    def __init__(self, todo: Todo, selected: tuple[str, int], **kwargs):
        super().__init__()
        self.todo = todo
        self.selected = selected
        self.kwargs = kwargs
    
    @discord.ui.button(label="Back", custom_id="back", style=discord.ButtonStyle.blurple)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        nembed = Embed(interaction, title="Marking Task Imporant", description=f"proposed by {interaction.user}", color=BOT_COLOR)
        for idx, day in enumerate(self.todo.data.values()):
            eventStr = "\n".join(day.listView(pointedEvent=0-int(idx != 0), col=False).split("\n")[1:-1])
            nembed.add_field(name=day.date, value=eventStr, inline=False)
        await interaction.message.edit(embed=nembed, view=SelectView(self.todo, ImportantView, markimportantOnView))
        await interaction.response.defer()
        logMsg(f"<ImportantView>.Back -> {self.selected}")

@bot.event
async def on_ready():
    logMsg(f'Bot has connected to Discord, server ID: {serverID}!')
    if len(sys.argv) > 1 and sys.argv[1] in ["-s", "--sync", "sync"]:
        await tree.sync(guild=server)
        logMsg(f"Synced commadn tree in {serverID}")
    return

@tree.command(name="sync", description="sync the command tree (sudoers only)", guild=server)
async def sync(interaction):
    logCommand(interaction.user, "sync")
    if interaction.user.id not in sudoers:
        await interaction.response.send_message(embed=errorMsg(interaction, "You are not allowed to use this command", type="warning"))
        return
    await interaction.response.send_message(embed=Embed(interaction, title="Synced", description="Synced the data", color=BOT_COLOR))
    await tree.sync(guild=server)
    return

@tree.command(name="sleep", description="Putin the bot to sleep (sudoers only)", guild=server)
async def sleep(interaction):
    logCommand(interaction.user, "sleep")
    if interaction.user.id not in sudoers:
        await interaction.response.send_message(embed=errorMsg(interaction, "You are not allowed to use this command", type="warning"))
        return
    embed = Embed(interaction, title="Zzz...", description=f"Shutdown by {interaction.user}", color=BOT_COLOR)
    await interaction.response.send_message(embed=embed)
    await bot.close()
    return

@tree.command(name="help", description="Show help", guild=server)
async def help(interaction):
    logCommand(interaction.user, "help")
    embed = Embed(interaction, title="Help", description="Commands", color=BOT_COLOR)
    embed.add_field(name="/help", value="Show this message", inline=False)
    embed.add_field(name="/add day: task: [description:] [tags:]", value="Add a new task", inline=False)
    embed.add_field(name="/delete date:", value="Delete a task", inline=False)
    embed.add_field(name="/list [date:]", value="List all tasks", inline=False)
    embed.add_field(name="/detailed [date:] [tag:] [hide_done:]", value="List all tasks including all details", inline=False)
    embed.add_field(name="/today [tag:] [hide_done:]", value="List all tasks for today", inline=False)
    embed.add_field(name="/done date:", value="Mark a task as done", inline=False)
    embed.add_field(name="/undone date:", value="Mark a task as not yet done", inline=False)
    embed.add_field(name="/important date:", value="Mark a task as important", inline=False)
    embed.add_field(name="/sleep", value="Shutdown the bot (sudoers only)", inline=False)
    embed.add_field(name="/sync", value="Sync the command tree (sudoers only)", inline=False)
    await interaction.response.send_message(embed=embed)
    return

@tree.command(name="add", description="Add a new todo", guild=server)
@app_commands.describe(
    day="Day of the month when the task is due in format YYYY-MM-DD",
    task="Task name",
    description="Task description",
    tags="Task tags, separated by \", \"",
)
async def add(interaction: discord.Interaction, day: str, task: str, description: str = "", tags: str = ""):
    logCommand(interaction.user, "add")
    logMsg(f"Day: {day}\nTask: {task}\nDescription: {description}\nTags: {tags}")
    tags = tags.split(", ")
    err = checkValidFormat(day, ctype="bot")
    if err:
        await interaction.response.send_message(embed=errorMsg(interaction, err))
        return
    if day < getTODAY():
        await interaction.response.send_message(embed=errorMsg(interaction, "Can't add tasks to past dates", type="warning"))
        return
    todo.addEvent(day, {
        "title": task,
        "description": description,
        "tags": tags,
        "status": False
    })
    embed = Embed(interaction, title="Task added", description=f"{day}", color=BOT_COLOR)
    embed.add_field(name="Task", value=task, inline=False)
    embed.add_field(name="Description", value=description, inline=False)
    embed.add_field(name="Tags", value=", ".join(tags), inline=False)
    await interaction.response.send_message(embed=embed)
    return

@tree.command(name="delete", description="Delete a todo", guild=server)
@app_commands.describe(
    date="Day of the month when the task is due in format YYYY-MM-DD, type \"-\" if you don want to set a specific day",
)
async def delete(interaction: discord.Interaction, date: str):
    logCommand(interaction.user, "delete", date=date)
    err = checkValidFormat(date, ctype="bot")
    if not err: 
        if date < getTODAY():
            await interaction.response.send_message(embed=errorMsg(interaction, "Can't delete tasks from past dates", type="warning"))
            return
        if date not in todo.data:
            await interaction.response.send_message(embed=errorMsg(interaction, "No tasks found for this day", type="warning"))
            return
    else:
        date = "-"
    embed = Embed(interaction, title="Deleting Task", description=f"proposed by {interaction.user}", color=BOT_COLOR)
    embed.clear_fields()
    for idx, day in enumerate(todo.data.values()):
        if day.date == date or date == "-":
            eventStr = "\n".join(day.listView(pointedEvent=0-int(idx != 0)+int(day.date == date and idx != 0), col=False).split("\n")[1:-1])
            embed.add_field(name=day.date, value=eventStr, inline=False)
    await interaction.response.send_message(embed=embed, view=SelectView(todo, DeleteConfirmation, deleteOnView, day=date))
    return

@tree.command(name="list", description="List all todos", guild=server)
@app_commands.describe(
    date="Day of the month when the task is due in format YYYY-MM-DD, type \"-\" if you don want to set a specific day",
    tag="Tag to filter tasks"
)
async def listView(interaction: discord.Interaction, date: str = "-", tag: str = ""):
    logCommand(interaction.user, "list", date=date, tag=tag)
    err = checkValidFormat(date, ctype="bot")
    if err and date != "-":
        await interaction.response.send_message(embed=errorMsg(interaction, err))
        return
    if (date not in todo.data and date not in todo.archived) and date != "-":
        embed = Embed(interaction, title="Tasks", description=f"List View", color=BOT_COLOR)
        embed.add_field(name=date, value="No tasks found for this day", inline=False)
        await interaction.response.send_message(embed=embed)
        return
    embed = Embed(interaction, title="Tasks", description=f"List View", color=BOT_COLOR)
    embed.clear_fields()
    if date != "-":
        if date in todo.archived:
            eventStr = "\n".join(todo.archived[date].listView(tag=(tag if tag != "" else None), col=False).split("\n")[1:-1])
            embed.add_field(name=date, value=eventStr, inline=False)
    for idx, day in enumerate(todo.data.values()):
        if day.date == date or date == "-":
            eventStr = "\n".join(day.listView(tag=(tag if tag != "" else None), col=False).split("\n")[1:-1])
            embed.add_field(name=day.date, value=eventStr, inline=False)
    await interaction.response.send_message(embed=embed)
    return

@tree.command(name="detailed", description="List all todos including all details", guild=server)
@app_commands.describe(
    date="Day of the month when the task is due in format YYYY-MM-DD, type \"-\" if you don want to set a specific day",
    tag="Tag to filter tasks",
    hide_done="Hide done tasks"
)
@app_commands.choices(
    hide_done=[
        app_commands.Choice(name="True", value="True"),
        app_commands.Choice(name="False", value="False")
    ]
)
async def detailed(interaction: discord.Interaction, date: str = "-", tag: str = "", hide_done: str = "False"):
    logCommand(interaction.user, "detailed", date=date, tag=tag, hide_done=hide_done)
    hideDone = (hide_done == "True")
    err = checkValidFormat(date, ctype="bot")
    if err and date != "-":
        await interaction.response.send_message(embed=errorMsg(interaction, err))
        return
    if (date not in todo.data and date not in todo.archived) and date != "-":
        embed = Embed(interaction, title="Tasks", description=f"List View", color=BOT_COLOR)
        embed.add_field(name=date, value="No tasks found for this day", inline=False)
        await interaction.response.send_message(embed=embed)
        return
    embed = Embed(interaction, title="Tasks", description=f"Detailed View", color=BOT_COLOR)
    embed.clear_fields()
    if date != "-":
        if date in todo.archived:
            eventStr = "\n".join(todo.archived[date].detailedView(tag=(tag if tag != "" else None), hideDone=hideDone, col=False).split("\n")[1:-1])
            embed.add_field(name=date, value=eventStr, inline=False)
    for idx, day in enumerate(todo.data.values()):
        if day.date == date or date == "-":
            eventStr = "\n".join(day.detailedView(tag=(tag if tag != "" else None), hideDone=hideDone, col=False).split("\n")[1:-1])
            embed.add_field(name=day.date, value=eventStr, inline=False)
    await interaction.response.send_message(embed=embed)
    return

@tree.command(name="today", description="List all todos for today", guild=server)
@app_commands.describe(
    tag="Tag to filter tasks",
    hide_done="Hide done tasks"
)
@app_commands.choices(
    hide_done=[
        app_commands.Choice(name="True", value="True"),
        app_commands.Choice(name="False", value="False")
    ]
)
async def today(interaction: discord.Interaction, tag: str = "", hide_done: str = "True"):
    logCommand(interaction.user, "today", tag=tag, hide_done=hide_done)
    hideDone = (hide_done == "True")
    embed = Embed(interaction, title="Tasks", description=f"task for {getTODAY()}", color=BOT_COLOR)
    embed.clear_fields()
    eventStr = "\n".join(todo.data[getTODAY()].detailedView(tag=(tag if tag != "" else None), hideDone=hideDone, col=False).split("\n")[1:-1]) if getTODAY() in todo.data and len([event for event in todo.data[getTODAY()].events if not event.status]) > 0 else "No unfinished tasks for today!"
    embed.add_field(name=getTODAY(), value=eventStr, inline=False)
    await interaction.response.send_message(embed=embed)
    return

@tree.command(name="done", description="Mark a task as done", guild=server)
@app_commands.describe(
    date="Day of the month when the task is due in format YYYY-MM-DD, type \"-\" if you don want to set a specific day"
)
async def done(interaction: discord.Interaction, date: str):
    logCommand(interaction.user, "done", date=date)
    err = checkValidFormat(date, ctype="bot")
    if not err: 
        if date < getTODAY():
            await interaction.response.send_message(embed=errorMsg(interaction, "Can't mark tasks from past dates as done", type="warning"))
            return
        if date not in todo.data:
            await interaction.response.send_message(embed=errorMsg(interaction, "No tasks found for this day", type="warning"))
            return
    else:
        date = "-"
    embed = Embed(interaction, title="Marking Task Done", description=f"proposed by {interaction.user}", color=BOT_COLOR)
    embed.clear_fields()
    for idx, day in enumerate(todo.data.values()):
        if day.date == date or date == "-":
            eventStr = "\n".join(day.listView(pointedEvent=0-int(idx != 0)+int(day.date == date and idx != 0), col=False).split("\n")[1:-1])
            embed.add_field(name=day.date, value=eventStr, inline=False)
    await interaction.response.send_message(embed=embed, view=SelectView(todo, DoneView, markdoneOnView, day=date))
    return

@tree.command(name="undone", description="Mark a task as not yet done", guild=server)
@app_commands.describe(
    date="Day of the month when the task is due in format YYYY-MM-DD, type \"-\" if you don want to set a specific day"
)
async def done(interaction: discord.Interaction, date: str):
    logCommand(interaction.user, "undone", date=date)
    err = checkValidFormat(date, ctype="bot")
    if not err: 
        if date < getTODAY():
            await interaction.response.send_message(embed=errorMsg(interaction, "Can't mark tasks from past dates as undone", type="warning"))
            return
        if date not in todo.data:
            await interaction.response.send_message(embed=errorMsg(interaction, "No tasks found for this day", type="warning"))
            return
    else:
        date = "-"
    embed = Embed(interaction, title="Marking Task unDone", description=f"proposed by {interaction.user}", color=BOT_COLOR)
    embed.clear_fields()
    for idx, day in enumerate(todo.data.values()):
        if day.date == date or date == "-":
            eventStr = "\n".join(day.listView(pointedEvent=0-int(idx != 0)+int(day.date == date and idx != 0), col=False).split("\n")[1:-1])
            embed.add_field(name=day.date, value=eventStr, inline=False)
    await interaction.response.send_message(embed=embed, view=SelectView(todo, unDoneView, markundoneOnView, day=date))
    return

@tree.command(name="important", description="Mark a task as important", guild=server)
@app_commands.describe(
    date="Day of the month when the task is due in format YYYY-MM-DD, type \"-\" if you don want to set a specific day"
)
async def done(interaction: discord.Interaction, date: str):
    logCommand(interaction.user, "important", date=date)
    err = checkValidFormat(date, ctype="bot")
    if not err: 
        if date < getTODAY():
            await interaction.response.send_message(embed=errorMsg(interaction, "Can't mark tasks from past dates as important", type="warning"))
            return
        if date not in todo.data:
            await interaction.response.send_message(embed=errorMsg(interaction, "No tasks found for this day", type="warning"))
            return
    else:
        date = "-"
    embed = Embed(interaction, title="Marking Task Important", description=f"proposed by {interaction.user}", color=BOT_COLOR)
    embed.clear_fields()
    for idx, day in enumerate(todo.data.values()):
        if day.date == date or date == "-":
            eventStr = "\n".join(day.listView(pointedEvent=0-int(idx != 0)+int(day.date == date and idx != 0), col=False).split("\n")[1:-1])
            embed.add_field(name=day.date, value=eventStr, inline=False)
    await interaction.response.send_message(embed=embed, view=SelectView(todo, ImportantView, markimportantOnView, day=date))
    return


bot.run(os.getenv("TOK"))