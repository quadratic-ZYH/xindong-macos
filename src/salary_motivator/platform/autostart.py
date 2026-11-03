"""Register or inspect login startup using the current user's OS settings."""
import os
import plistlib
from pathlib import Path
import subprocess
import sys

from ..model import CONFIG_HOME, AUTOSTART_NAME

PACKAGE_DIRECTORY = Path(__file__).resolve().parents[1]
MAC_AGENT_LABEL = "io.github.wizzenh.xindong"
MAC_AGENT_PATH = Path.home() / "Library" / "LaunchAgents" / f"{MAC_AGENT_LABEL}.plist"


def startup_command():
    executable = Path(sys.executable)
    if sys.platform == "darwin" and getattr(sys, "frozen", False):
        # Use Launch Services so login startup and double-clicks share one app.
        return ["/usr/bin/open", "-a", str(executable.parents[2])]
    if os.name == "nt":
        launcher = PACKAGE_DIRECTORY.parent.parent / "SalaryMotivator.exe"
        if launcher.is_file():
            return [str(launcher)]
        windowed = executable.with_name("pythonw.exe")
        if windowed.is_file():
            executable = windowed
    elif PACKAGE_DIRECTORY.parent == Path("/usr/share/salary-motivator"):
        return ["/usr/bin/salary-motivator"]

    source_launcher = PACKAGE_DIRECTORY.parent.parent / "scripts/run.py"
    if PACKAGE_DIRECTORY.parent.name == "src" and source_launcher.is_file():
        return [str(executable), str(source_launcher)]
    return [str(executable), "-m", "salary_motivator"]


def autostart_enabled():
    if sys.platform == "darwin":
        try:
            with MAC_AGENT_PATH.open("rb") as handle:
                agent = plistlib.load(handle)
            return agent.get("Label") == MAC_AGENT_LABEL and not agent.get("Disabled", False)
        except (OSError, ValueError, plistlib.InvalidFileException):
            return False
    if os.name == "nt":
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
            ) as key:
                return bool(winreg.QueryValueEx(key, "SalaryMotivator")[0])
        except FileNotFoundError:
            return False
    candidates = [CONFIG_HOME / "autostart" / AUTOSTART_NAME]
    candidates += [
        Path(folder) / "autostart" / AUTOSTART_NAME
        for folder in os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(":")
        if folder
    ]
    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        lines = {line.strip().lower() for line in content.splitlines()}
        return (
            "hidden=true" not in lines
            and "x-gnome-autostart-enabled=false" not in lines
        )
    return False


def set_autostart(enabled):
    if sys.platform == "darwin":
        if not enabled:
            MAC_AGENT_PATH.unlink(missing_ok=True)
            subprocess.run(
                ["/bin/launchctl", "bootout", f"gui/{os.getuid()}/{MAC_AGENT_LABEL}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
            )
            return
        MAC_AGENT_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary = MAC_AGENT_PATH.with_suffix(".tmp")
        with temporary.open("wb") as handle:
            plistlib.dump({
                "Label": MAC_AGENT_LABEL,
                "ProgramArguments": startup_command(),
                "RunAtLoad": True,
                "LimitLoadToSessionType": "Aqua",
                "ProcessType": "Interactive",
            }, handle)
        temporary.replace(MAC_AGENT_PATH)
        return
    if os.name == "nt":
        import winreg

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"
        ) as key:
            if enabled:
                winreg.SetValueEx(
                    key,
                    "SalaryMotivator",
                    0,
                    winreg.REG_SZ,
                    subprocess.list2cmdline(startup_command()),
                )
            else:
                try:
                    winreg.DeleteValue(key, "SalaryMotivator")
                except FileNotFoundError:
                    pass
        return
    path = CONFIG_HOME / "autostart" / AUTOSTART_NAME
    path.parent.mkdir(parents=True, exist_ok=True)

    def quote(value):
        value = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("`", "\\`")
            .replace("$", "\\$")
            .replace("%", "%%")
        )
        return '"' + value + '"'

    command = " ".join(quote(arg) for arg in startup_command())
    content = (
        "[Desktop Entry]\nType=Application\nName=Salary Motivator\n"
        "Name[zh_CN]=上班鼓励器\nExec="
        + command
        + "\nTryExec="
        + startup_command()[0]
        + "\nTerminal=false\n"
        "Hidden="
        + ("false" if enabled else "true")
        + "\nX-GNOME-Autostart-enabled="
        + ("true" if enabled else "false")
        + "\n"
    )
    temporary = path.with_suffix(".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
