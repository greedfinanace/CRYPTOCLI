import sys
import os

class InputHandler:
    def __init__(self):
        self.is_windows = os.name == 'nt'
        if self.is_windows:
            import msvcrt
            self.msvcrt = msvcrt
        else:
            import select
            import tty
            import termios
            self.select = select
            self.tty = tty
            self.termios = termios
            self.old_settings = None

    def __enter__(self):
        if not self.is_windows:
            try:
                self.old_settings = self.termios.tcgetattr(sys.stdin)
                self.tty.setcbreak(sys.stdin.fileno())
            except Exception:
                # Fallback for non-interactive or testing environments
                pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.is_windows and self.old_settings:
            self.termios.tcsetattr(sys.stdin, self.termios.TCSADRAIN, self.old_settings)

    def get_key(self):
        if self.is_windows:
            if self.msvcrt.kbhit():
                ch = self.msvcrt.getch()
                try:
                    return ch.decode('utf-8')
                except:
                    return None
        else:
            if self.old_settings: # Only if successfully initialized
                if self.select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                    return sys.stdin.read(1)
        return None
