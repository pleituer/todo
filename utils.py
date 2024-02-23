import datetime

from config import CONFIG

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

TODAY = datetime.date.today().strftime(f"%Y{CONFIG['dateSeperator']}%m{CONFIG['dateSeperator']}%d")