"""Real Aqua integration checks with temporary settings and LaunchAgent files."""
import datetime as dt
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

if sys.platform != "darwin":
    raise SystemExit("This check requires macOS.")


with tempfile.TemporaryDirectory(prefix="salary-macos-") as temporary:
    os.environ["XDG_CONFIG_HOME"] = temporary
    from AppKit import NSApplication
    from salary_motivator.app import SalaryWidget
    from salary_motivator import model
    from salary_motivator.platform import autostart, window_chrome

    autostart.MAC_AGENT_PATH = Path(temporary) / "LaunchAgents" / "test.plist"
    autostart.MAC_AGENT_LABEL += f".test.{os.getpid()}"
    app = SalaryWidget(sync_calendar=False)

    def pump(predicate, timeout=5):
        limit = time.monotonic() + timeout
        while time.monotonic() < limit:
            app.root.update()
            if predicate():
                return
            time.sleep(0.02)
        raise AssertionError("Aqua state did not settle")

    try:
        pump(lambda: app.tray.ready)
        assert app.tray.error is None, app.tray.error
        assert app.root.state() == "withdrawn"
        assert NSApplication.sharedApplication().activationPolicy() == 1
        native = app.tray.native
        assert native.item.isVisible()
        assert native.menu.numberOfItems() == 4
        assert not app.root.overrideredirect()
        assert "titled" not in app.root.attributes("-stylemask")
        assert abs(app.root.attributes("-alpha") - 0.9) < 0.01
        left, top, right, bottom = window_chrome.work_area(app.root)
        assert left <= app.root.winfo_x() < right
        assert top <= app.root.winfo_y() < bottom
        # The real Cocoa target/action path must return control to Tk.
        cocoa = NSApplication.sharedApplication()
        cocoa.sendAction_to_from_("toggleCounter:", native.target, native.item.button())
        pump(lambda: app.root.state() == "normal")
        assert not app.hidden_to_tray
        from decimal import Decimal
        from AppKit import NSApplicationDidResignActiveNotification
        from Foundation import NSNotificationCenter
        native.update_income(Decimal("123.4567"), "工作中")
        assert native.item.button().title() == "¥123.4567"
        native.update_income(Decimal("123.4582"), "工作中")
        assert native.item.button().title() == "¥123.4582"
        test_time = dt.datetime(2026, 11, 3, 16, 30)
        app.render_earnings(test_time)
        assert "下班 3,600秒" in native.item.button().title()
        assert app.goals.item.name not in native.item.button().title()
        assert app.goals.item.name not in native.item.button().toolTip()
        assert app.canvas.itemcget(app.countdown_id, "text") == "3,600 秒"
        assert "参考价" in app.canvas.itemcget(app.goal_price_id, "text")
        assert "计薪秒" in app.canvas.itemcget(app.goal_eta_id, "text")
        assert top <= app.root.winfo_y() <= bottom - app.HEIGHT
        app.render_earnings(test_time + dt.timedelta(seconds=1))
        assert "下班 3,599秒" in native.item.button().title()
        previous = app.goals.item
        app.goals.balance = previous.price - Decimal("0.001")
        completed = app.goals.completed
        app.goals.advance(app.goals.last_time + dt.timedelta(seconds=1), app.config)
        app.render_earnings(test_time)
        assert app.goals.item.id != previous.id and app.goals.completed == completed + 1
        assert app.canvas.itemcget(app.goal_name_id, "text") == app.goals.item.name
        for _ in range(3):
            cocoa.sendAction_to_from_("toggleCounter:", native.target, native.item.button())
            pump(lambda: app.root.state() == "withdrawn")
            cocoa.sendAction_to_from_("toggleCounter:", native.target, native.item.button())
            pump(lambda: app.root.state() == "normal")
        NSNotificationCenter.defaultCenter().postNotificationName_object_(NSApplicationDidResignActiveNotification, cocoa)
        pump(lambda: app.root.state() == "withdrawn")
        cocoa.sendAction_to_from_("openSettings:", native.target, native.menu.itemAtIndex_(1))
        pump(lambda: app.dialog is not None and app.dialog.winfo_exists())
        dialog = app.dialog
        dialog.appearance.opacity.set(70)
        app.root.update()
        assert abs(app.root.attributes("-alpha") - 0.7) < 0.01
        dialog.cancel()
        app.root.update()
        assert app.root.focus_displayof() == app.root
        assert abs(app.root.attributes("-alpha") - 0.9) < 0.01
        app.settings()
        dialog = app.dialog
        dialog.form["monthly"].set("12345")
        dialog.appearance.theme_key.set("morandi")
        dialog.appearance.opacity.set(82)
        chosen = dt.date(dialog.year, dialog.month, 1)
        dialog.toggle_workday(chosen)
        dialog.save()
        saved = model.load_settings()
        assert saved["monthly"] == "12345" and saved["theme"] == "morandi"
        assert saved["opacity"] == 82 and chosen.isoformat() in saved["overrides"]
        # Verify syntax and executable paths, without enabling personal login startup.
        autostart.set_autostart(True)
        assert autostart.autostart_enabled()
        with autostart.MAC_AGENT_PATH.open("rb") as handle:
            agent = plistlib.load(handle)
        assert Path(agent["ProgramArguments"][0]).exists()
        subprocess.run(["/usr/bin/plutil", "-lint", str(autostart.MAC_AGENT_PATH)], check=True)
        autostart.set_autostart(False)
        assert not autostart.autostart_enabled()
        app.hide_to_tray()
        pump(lambda: app.hidden_to_tray)
        app.root.tk.call("::tk::mac::ReopenApplication")
        pump(lambda: app.root.state() == "normal")
        cocoa.sendAction_to_from_("quitCounter:", native.target, native.menu.itemAtIndex_(3))
        pump(lambda: app.closed)
        assert native.item is None
        print("PASS: background-only start, no Dock, live menu-bar income, anchored panel toggle x3, "
              "outside-click dismissal, hide/reopen, opacity preview/cancel/save, salary/calendar persistence, "
              "LaunchAgent plist, clean menu-bar removal and quit")
    finally:
        if not app.closed:
            app.quit()
