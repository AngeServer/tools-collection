"""
Copyright (c) 2023 SERVER (also known as Angolmois)
This software is released under the MIT License, see LICENSE.
"""
import ctypes
import io
import os
import sys


# Colors
class TerminalColor:
    RESET = "\x1b[0m"

    @staticmethod
    def code(num: int) -> str:
        return f"\x1b[{str(num).zfill(3)}m"

# Util Functions
class TerminalUtil:

    @staticmethod
    def set_text_io_wrapper(encoding:str="utf-8"):
        sys.stdout = io.TextIOWrapper(buffer=sys.stdout.buffer, encoding=encoding)
        sys.stderr = io.TextIOWrapper(buffer=sys.stderr.buffer, encoding=encoding)

    @staticmethod
    def set_ansimode_if_windows():
        if os.name == "nt":
            handle = ctypes.windll.kernel32.GetStdGHandle(-11)
            ctypes.windll.kernel32.setConsoleMode(handle, 0x0007)

    @staticmethod
    def show_terminal_colors():
        print("#========================================#")
        print("#===== Terminal Color Code(000-099) =====#")
        print("#========================================#")
        for i in range(10):
            for j in range(10):
                n = i * 10 + j
                v = str(n).zfill(3)
                print(f"{TerminalColor.code(n)}{v}{TerminalColor.RESET}", end=" ")
            print("")
        print("#========================================#")


# TerminalUtil.show_terminal_colors()