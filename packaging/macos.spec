# Build with: python -m PyInstaller packaging/macos.spec
from pathlib import Path
import re
import subprocess

root = Path(SPECPATH).parent
analysis = Analysis(
    [str(root / "scripts/run-macos.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[(str(root / "src/salary_motivator/assets"), "salary_motivator/assets"),
           (str(root / "LICENSE"), "licenses"),
           (str(root / "ATTRIBUTION.md"), "licenses"),
           (str(root / "third_party/licenses"), "licenses/third_party"),
           (str(root / "README.md"), "licenses")],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
    noarchive=False,
)
# X11 is only used by the retained Linux platform branch, never by Aqua.
analysis.binaries = [entry for entry in analysis.binaries
                     if not Path(entry[0]).name.startswith(("libX11", "libXau", "libXdmcp", "libxcb"))]
minimum_os = (13, 0)
for source in sorted({entry[1] for entry in analysis.binaries}):
    result = subprocess.run(["/usr/bin/vtool", "-arch", "arm64", "-show-build", source],
                            capture_output=True, text=True)
    for value in re.findall(r"\bminos\s+([0-9.]+)", result.stdout):
        minimum_os = max(minimum_os, tuple(int(part) for part in value.split(".")))
minimum_os_text = ".".join(str(part) for part in minimum_os)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, [], exclude_binaries=True, name="薪动",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, argv_emulation=False, target_arch="arm64", codesign_identity=None,
    entitlements_file=None,
)
collection = COLLECT(exe, analysis.binaries, analysis.datas, strip=False, upx=False, name="薪动")
app = BUNDLE(
    collection, name="薪动.app", icon=str(root / "src/salary_motivator/assets/icon.png"),
    bundle_identifier="io.github.wizzenh.xindong", version="1.4.0",
    info_plist={
        "CFBundleDisplayName": "薪动",
        "CFBundleName": "薪动",
        "CFBundleShortVersionString": "1.4.0",
        "LSUIElement": True,
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleLocalizations": ["zh_CN", "en"],
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": minimum_os_text,
        "NSHumanReadableCopyright": "Copyright © 2026 WizzenH; macOS enhancements © 2026 quadratic-ZYH. MIT License.",
    },
)
