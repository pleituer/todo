import re
import datetime

from config import CONFIG
import pytz

def hexToRGBString(hexString):
    try:
        return f"\x1b[38;2;{int(hexString[1:3], 16)};{int(hexString[3:5], 16)};{int(hexString[5:7], 16)}m"
    except ValueError:
        return ""

def tagColorWrap(tag):
    if tag in CONFIG["tagColors"]:
        return hexToRGBString(CONFIG["tagColors"][tag])+tag+"\x1b[0m"
    else:
        return tag

def getTODAY(): 
    utc_plus_8 = pytz.timezone('Etc/GMT-8')
    return datetime.datetime.now(utc_plus_8).strftime(f"%Y{CONFIG['dateSeperator']}%m{CONFIG['dateSeperator']}%d")

dateRegex = r"^\d{4}"+CONFIG["dateSeperator"]+r"\d{2}"+CONFIG["dateSeperator"]+r"\d{2}$"
dateRegex2 = r"^\d{4}"+CONFIG["dateSeperator"]+r"\d{2}$"

def checkValidFormat(dateString, regex=dateRegex, ctype="main"):
    if not re.match(regex, dateString):
        if ctype == "main":
            print("Invalid date format. Use YYYY"+CONFIG["dateSeperator"]+"MM"+CONFIG["dateSeperator"]+"DD")
            exit()
        return "Invalid date format. Use YYYY"+CONFIG["dateSeperator"]+"MM"+CONFIG["dateSeperator"]+"DD"
    elif int(dateString.split(CONFIG["dateSeperator"])[1]) > 12 or (len(dateString.split(CONFIG["dateSeperator"])) > 2 and int(dateString.split(CONFIG["dateSeperator"])[2]) > 31):
        if ctype == "main":
            print("Invalid date")
            exit()
        return "Invalid date"
    
DISCORD_MODE = True