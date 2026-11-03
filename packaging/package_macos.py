#!/usr/bin/env python3
"""Package a signed local app into a DMG, ZIP, tracked-source ZIP and checksums."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--output", default=ROOT / "dist/release", type=Path)
    args = parser.parse_args()
    app = args.app.resolve()
    output = args.output.resolve()
    info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
    version = info["CFBundleShortVersionString"]
    minimum = info["LSMinimumSystemVersion"]
    run(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app)])
    output.mkdir(parents=True, exist_ok=True)
    name = f"SalaryMotivator-{version}-macos-arm64"
    instructions = (
        f"薪动 {version} · Apple Silicon ARM64\n\n"
        f"本安装包最低要求 macOS {minimum}。\n"
        "1. 先退出旧版薪动。\n2. 把薪动.app 拖入 Applications。\n"
        "3. 从应用程序启动；默认在右上角菜单栏运行，单击金额展开面板。\n\n"
        "本应用使用本地临时签名，未做 Apple 开发者签名或公证。\n"
        "请核对来源和 SHA256SUMS.txt，必要时参考 Apple 官方说明：\n"
        "https://support.apple.com/en-gb/102445\n\n"
        "项目：https://github.com/quadratic-ZYH/xindong-macos\n"
        "基于：https://github.com/WizzenH/xindong （MIT）\n"
        "调休数据：https://github.com/NateScarlet/holiday-cn （MIT）\n\n"
        "升级保留工资设置与目标进度。物品价格为趣味参考估值，不发生真实购买。\n"
    )
    with tempfile.TemporaryDirectory(prefix="xindong-dmg-") as temp:
        stage = Path(temp) / "image"
        stage.mkdir()
        run(["/usr/bin/ditto", str(app), str(stage / app.name)])
        (stage / "Applications").symlink_to("/Applications", target_is_directory=True)
        (stage / "安装说明.txt").write_text(instructions, encoding="utf-8")
        shutil.copy2(ROOT / "LICENSE", stage / "LICENSE.txt")
        run(["/usr/bin/hdiutil", "create", "-ov", "-format", "UDZO", "-fs", "HFS+",
             "-volname", f"薪动 {version}", "-srcfolder", str(stage), str(output / f"{name}.dmg")],
            stdout=subprocess.DEVNULL)
    run(["/usr/bin/ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(app), str(output / f"{name}.zip")])
    source = output / f"xindong-macos-{version}-source.zip"
    run(["git", "archive", "--format=zip", f"--prefix=xindong-macos-{version}/", "HEAD", "-o", str(source)], cwd=ROOT)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    (output / "BUILD-INFO.json").write_text(json.dumps({
        "version": version, "source_commit": commit,
        "repository": "https://github.com/quadratic-ZYH/xindong-macos",
        "upstream": "https://github.com/WizzenH/xindong",
        "holiday_data": "https://github.com/NateScarlet/holiday-cn",
        "architecture": "arm64", "minimum_macos": minimum,
        "build_macos": platform.mac_ver()[0], "python": platform.python_version(),
        "signature": "ad-hoc", "apple_notarized": False,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = [output / f"{name}.dmg", output / f"{name}.zip", source, output / "BUILD-INFO.json"]
    checksums = "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in files)
    (output / "SHA256SUMS.txt").write_text(checksums, encoding="utf-8")
    print(checksums)


if __name__ == "__main__":
    main()
