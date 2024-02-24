UP = "UP"
DOWN = "DOWN"
LEFT = "LEFT"
RIGHT = "RIGHT"
INVALID = "INVALID"
ENTER = "ENTER"

try:
    import msvcrt
    isWindows = True
except ImportError:
    import termios, sys, tty, select
    isWindows = False

class Input():
    def __init__(self, t=-1, showCursor=False):
        if not showCursor: print("\x1b[?25l", end="")
        self.t = t
        if not isWindows:
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setcbreak(sys.stdin.fileno())
    
    def __del__(self):
        print("\x1b[?25h", end="")
        if not isWindows:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)
        
    def getch(self):
        if isWindows:
            if not msvcrt.kbhit(): 
                return ""
            ch = msvcrt.getch()
            if ch == b"\xe0":
                ch = msvcrt.getch()
                if ch == b"H":
                    return UP
                elif ch == b"P":
                    return DOWN
                elif ch == b"M":
                    return RIGHT
                elif ch == b"K":
                    return LEFT
                else:
                    return INVALID
            elif ch == b"\r":
                return ENTER
            return ch.decode("utf-8")
        else:
            r, w, x = select.select([sys.stdin], [], [], self.t)
            if r:
                ch = sys.stdin.read(1)
            else:
                ch = ""
            if ch == "\x1b":
                ch += sys.stdin.read(1)
                if ch == "\x1b[A":
                    return UP
                elif ch == "\x1b[B":
                    return DOWN
                elif ch == "\x1b[C":
                    return RIGHT
                elif ch == "\x1b[D":
                    return LEFT
                else:
                    return INVALID
            elif ch == "\r":
                return ENTER
            return ch
        