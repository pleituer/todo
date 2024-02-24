from config import CONFIG
from utils import hexToRGBString, tagColorWrap

class Event():
    def __init__(self, eventDict):
        self.title = eventDict['title']
        self.description = eventDict['description']
        self.tags = eventDict['tags']
        self.status = eventDict['status']
        if self.tags:
            if self.tags[0] == "-important-" and len(self.tags) > 1 and self.tags[1] in CONFIG["tagColors"]:
                self.tagColor = hexToRGBString(CONFIG["tagColors"][self.tags[1]])
            elif self.tags[0] != "-important-" and self.tags[0] in CONFIG["tagColors"]:
                self.tagColor = hexToRGBString(CONFIG["tagColors"][self.tags[0]])
            else:
                self.tagColor = ""
        else:
            self.tagColor = ""
        self.tagColor = "\x1b[0m" + self.tagColor
        if self.status: self.doneHex = hexToRGBString(CONFIG["tagColors"]["-done-"]) if "-done-" in CONFIG["tagColors"] else ""
        else: self.doneHex = hexToRGBString(CONFIG["tagColors"]["-undone-"]) if "-undone-" in CONFIG["tagColors"] else ""
        self.importantColor = "\x1b[0m" + (hexToRGBString(CONFIG["tagColors"]["-important-"]) if self.tags[0]=="-important-" and "-important-" in CONFIG["tagColors"] else "")
    def jsonify(self):
        return {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "status": self.status
        }
    def done(self):
        self.status = True
    def listView(self, arrow=False):
        return f"{'->' if arrow else '  '} {self.doneHex}[{CONFIG['done'] if self.status else ' '}] {self.importantColor}{CONFIG['important'] if self.tags[0] == '-important-' else ''}{self.tagColor}{self.title}\x1b[0m"
    def detailedView(self, idx=None):
        return f"""Task{f" {idx}" if idx is not None else ""}: {self.title}
Description: {self.description}
Tags: {', '.join(tagColorWrap(tag) for tag in self.tags)}
Done: {'Yes' if self.status else 'No'}"""
    def done(self):
        self.status = True
        self.doneHex = hexToRGBString(CONFIG["tagColors"]["-done-"]) if "-done-" in CONFIG["tagColors"] else ""
    def undone(self):
        self.status = False
        self.doneHex = hexToRGBString(CONFIG["tagColors"]["-done-"]) if "-undone-" in CONFIG["tagColors"] else ""
    def shorten(self, outputLength):
        rawStr = f"C[{CONFIG['done'] if self.status else ' '}] C{CONFIG['important'] if self.tags[0] == '-important-' else ''}C{self.title}"
        rawStr = (rawStr[:outputLength] + "\x1b[0m" + "...") if (len(rawStr)-3 > outputLength and outputLength >= 3) else (rawStr + " "*(outputLength-len(rawStr)+3) + "\x1b[0m")
        rawStr = rawStr.replace("C", self.doneHex, 1).replace("C", self.importantColor, 1).replace("C", self.tagColor, 1)
        return rawStr