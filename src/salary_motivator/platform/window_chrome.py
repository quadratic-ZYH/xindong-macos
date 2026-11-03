"""Keep a normal, minimizable OS window while removing its decorative frame."""
import ctypes as C
import ctypes.util
import os
import sys
import tkinter as tk


def work_area(root):
    """Return desktop bounds excluding panels, with a screen-size fallback."""
    fallback = (0, 0, root.winfo_screenwidth(), root.winfo_screenheight())
    if sys.platform == "darwin":
        from .macos import work_area as mac_work_area

        return mac_work_area()
    if os.name == "nt":
        from ctypes import wintypes as W

        rect = W.RECT()
        user = C.WinDLL("user32", use_last_error=True)
        if user.SystemParametersInfoW(0x0030, 0, C.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom
        return fallback

    x = C.CDLL(ctypes.util.find_library("X11") or "libX11.so.6")
    pointer, atom = C.c_void_p, C.c_ulong
    x.XOpenDisplay.argtypes = [C.c_char_p]
    x.XOpenDisplay.restype = pointer
    x.XDefaultRootWindow.argtypes = [pointer]
    x.XDefaultRootWindow.restype = atom
    x.XInternAtom.argtypes = [pointer, C.c_char_p, C.c_int]
    x.XInternAtom.restype = atom
    x.XGetWindowProperty.argtypes = [
        pointer,
        atom,
        atom,
        C.c_long,
        C.c_long,
        C.c_int,
        atom,
        C.POINTER(atom),
        C.POINTER(C.c_int),
        C.POINTER(atom),
        C.POINTER(atom),
        C.POINTER(pointer),
    ]
    x.XFree.argtypes = [pointer]
    x.XCloseDisplay.argtypes = [pointer]
    display = x.XOpenDisplay(None)
    if not display:
        return fallback

    def property_values(name):
        actual, count, remaining = atom(), atom(), atom()
        fmt, data = C.c_int(), pointer()
        key = x.XInternAtom(display, name, True)
        if not key:
            return []
        try:
            result = x.XGetWindowProperty(
                display,
                x.XDefaultRootWindow(display),
                key,
                0,
                4096,
                False,
                6,
                C.byref(actual),
                C.byref(fmt),
                C.byref(count),
                C.byref(remaining),
                C.byref(data),
            )
            if result or actual.value != 6 or fmt.value != 32 or not data:
                return []
            return list(C.cast(data, C.POINTER(atom))[: count.value])
        finally:
            if data:
                x.XFree(data)

    try:
        desktop = property_values(b"_NET_CURRENT_DESKTOP") or [0]
        areas = property_values(b"_NET_WORKAREA")
        offset = desktop[0] * 4
        if offset + 4 <= len(areas):
            left, top, width, height = areas[offset : offset + 4]
            if width > 0 and height > 0:
                return left, top, left + width, top + height
        return fallback
    finally:
        x.XCloseDisplay(display)


def undecorate(root):
    if sys.platform == "darwin":
        # Tk 9 exposes Cocoa style masks directly. Keep minimization enabled
        # while removing the titlebar; Tk 8.6 uses the older Aqua command.
        try:
            root.attributes("-stylemask", ("miniaturizable",))
        except tk.TclError:
            root.tk.call("::tk::unsupported::MacWindowStyle", "style", root._w,
                         "document", ("noTitleBar", "collapseBox"))
        return
    root.update_idletasks()
    if os.name == "nt":
        from ctypes import wintypes as W

        user = C.WinDLL("user32", use_last_error=True)
        user.GetParent.argtypes = [W.HWND]
        user.GetParent.restype = W.HWND
        user.GetWindowLongW.argtypes = [W.HWND, C.c_int]
        user.GetWindowLongW.restype = W.LONG
        user.SetWindowLongW.argtypes = [W.HWND, C.c_int, W.LONG]
        user.SetWindowLongW.restype = W.LONG
        user.SetWindowPos.argtypes = [
            W.HWND,
            W.HWND,
            C.c_int,
            C.c_int,
            C.c_int,
            C.c_int,
            W.UINT,
        ]
        user.SetWindowPos.restype = W.BOOL
        hwnd = user.GetParent(root.winfo_id()) or root.winfo_id()
        style = user.GetWindowLongW(hwnd, -16)
        user.SetWindowLongW(hwnd, -16, (style & ~0x00C40000) | 0x000A0000)
        exstyle = user.GetWindowLongW(hwnd, -20)
        user.SetWindowLongW(hwnd, -20, (exstyle & ~0x80) | 0x40000)
        user.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0037)
        return
    # Tk on Linux uses X11 (or XWayland). Set Motif decoration hints on Tk's
    # wrapper, leaving override_redirect false so the WM can iconify it.
    x = C.CDLL(ctypes.util.find_library("X11") or "libX11.so.6")
    pointer = C.c_void_p
    window = C.c_ulong
    x.XOpenDisplay.argtypes = [C.c_char_p]
    x.XOpenDisplay.restype = pointer
    x.XQueryTree.argtypes = [
        pointer,
        window,
        C.POINTER(window),
        C.POINTER(window),
        C.POINTER(C.POINTER(window)),
        C.POINTER(C.c_uint),
    ]
    x.XQueryTree.restype = C.c_int
    x.XInternAtom.argtypes = [pointer, C.c_char_p, C.c_int]
    x.XInternAtom.restype = window
    x.XChangeProperty.argtypes = [
        pointer,
        window,
        window,
        window,
        C.c_int,
        C.c_int,
        pointer,
        C.c_int,
    ]
    x.XFree.argtypes = [pointer]
    x.XFlush.argtypes = [pointer]
    x.XCloseDisplay.argtypes = [pointer]
    display = x.XOpenDisplay(None)
    if not display:
        raise OSError("无法连接显示服务")
    try:
        parent, ancestor = window(), window()
        children = C.POINTER(window)()
        count = C.c_uint()
        if not x.XQueryTree(
            display,
            root.winfo_id(),
            C.byref(ancestor),
            C.byref(parent),
            C.byref(children),
            C.byref(count),
        ):
            raise OSError("无法获取窗口")
        if children:
            x.XFree(children)
        atom = x.XInternAtom(display, b"_MOTIF_WM_HINTS", False)
        hints = (C.c_ulong * 5)(2, 0, 0, 0, 0)
        x.XChangeProperty(
            display, parent.value, atom, atom, 32, 0, C.cast(hints, pointer), 5
        )
        x.XFlush(display)
    finally:
        x.XCloseDisplay(display)
