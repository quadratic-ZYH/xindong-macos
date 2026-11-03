"""Aqua integration. All Cocoa objects are created and used on Tk's main thread."""
from AppKit import (
    NSApplication, NSImage, NSMenu, NSMenuItem, NSScreen, NSStatusBar,
    NSVariableStatusItemLength, NSFont, NSFontWeightMedium,
    NSLeftMouseUpMask, NSRightMouseUpMask, NSRightMouseUp,
    NSApplicationDidResignActiveNotification, NSApplicationActivationPolicyAccessory,
)
from Foundation import NSObject, NSNotificationCenter


class SalaryMenuTarget(NSObject):
    def toggleCounter_(self, sender):
        event = NSApplication.sharedApplication().currentEvent()
        if event is not None and event.type() == NSRightMouseUp:
            self.owner.item.popUpStatusItemMenu_(self.owner.menu)
        else:
            self.events.put("toggle")

    def applicationDidResignActive_(self, notification):
        self.events.put("dismiss")

    def showCounter_(self, sender):
        self.events.put("show")

    def openSettings_(self, sender):
        self.events.put("settings")

    def quitCounter_(self, sender):
        self.events.put("quit")


class MenuBarIcon:
    def __init__(self, events):
        self.target = SalaryMenuTarget.alloc().init()
        self.target.events = events
        self.target.owner = self
        NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        self.item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        self.item.setAutosaveName_("SalaryMotivator.Income")
        button = self.item.button()
        button.setTitle_("¥0.0000 · 下班 --秒")
        button.setFont_(NSFont.monospacedDigitSystemFontOfSize_weight_(12, NSFontWeightMedium))
        button.setTarget_(self.target)
        button.setAction_("toggleCounter:")
        button.sendActionOn_(NSLeftMouseUpMask | NSRightMouseUpMask)
        button.setToolTip_("薪动 · 上班鼓励器")
        button.setAccessibilityLabel_("薪动，今日累计收入")
        self.menu = NSMenu.alloc().initWithTitle_("薪动")
        for title, action in (
            ("显示工资计数器", "showCounter:"),
            ("工资与外观设置…", "openSettings:"),
            (None, None),
            ("退出薪动", "quitCounter:"),
        ):
            if title is None:
                self.menu.addItem_(NSMenuItem.separatorItem())
            else:
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    title, action, ""
                )
                item.setTarget_(self.target)
                self.menu.addItem_(item)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self.target, "applicationDidResignActive:",
            NSApplicationDidResignActiveNotification, None,
        )
        self.last_title = None

    def update_income(self, amount, description, countdown=""):
        money = f"¥{amount:,.4f}"
        title = money + (f" · {countdown}" if countdown else "")
        button = self.item.button()
        if title != self.last_title:
            button.setTitle_(title)
            button.setAccessibilityValue_(title)
            self.last_title = title
        button.setToolTip_(f"薪动 · 今日累计 {money}\n{countdown}\n{description}\n单击展开 · 右键设置/退出")

    def panel_position(self, width, height):
        button = self.item.button()
        anchor = button.window().convertRectToScreen_(button.convertRect_toView_(button.bounds(), None))
        screen = button.window().screen() or NSScreen.screens()[0]
        visible = screen.visibleFrame()
        primary = NSScreen.screens()[0].frame()
        desktop_top = primary.origin.y + primary.size.height
        anchor_right = anchor.origin.x + anchor.size.width
        screen_top = screen.frame().origin.y + screen.frame().size.height
        if anchor.size.width <= 0 or not visible.origin.y + visible.size.height - 2 <= anchor.origin.y <= screen_top:
            anchor_right = visible.origin.x + visible.size.width
            anchor_y = visible.origin.y + visible.size.height
        else:
            anchor_y = anchor.origin.y
        x = max(visible.origin.x + 8, min(anchor_right - width,
                                        visible.origin.x + visible.size.width - width - 8))
        y = max(desktop_top - visible.origin.y - visible.size.height + 6,
                min(desktop_top - anchor_y + 6, desktop_top - visible.origin.y - height - 8))
        return round(x), round(y)

    def stop(self):
        NSNotificationCenter.defaultCenter().removeObserver_(self.target)
        if self.item is not None:
            NSStatusBar.systemStatusBar().removeStatusItem_(self.item)
            self.item = None
        self.menu = None
        self.target.owner = None
        self.target = None


def activate(root):
    app = NSApplication.sharedApplication()
    app.activateIgnoringOtherApps_(True)
    for window in app.windows():
        if window.title() == root.title() and window.canBecomeKeyWindow():
            window.makeKeyAndOrderFront_(None)
            break


def work_area():
    # Cocoa has a bottom-left origin; Tk uses the top-left of the main screen.
    primary = NSScreen.screens()[0]
    screen = NSScreen.mainScreen() or primary
    visible = screen.visibleFrame()
    top = primary.frame().origin.y + primary.frame().size.height
    return (
        int(visible.origin.x),
        int(top - visible.origin.y - visible.size.height),
        int(visible.origin.x + visible.size.width),
        int(top - visible.origin.y),
    )
