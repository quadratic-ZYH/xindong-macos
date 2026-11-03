# 薪动 · macOS 菜单栏版

让上班时间变成看得见的收入：右上角实时跳钱、下班倒计时，以及攒够自动切换的趣味物品目标。

**本仓库基于 [WizzenH/xindong](https://github.com/WizzenH/xindong) 派生开发**，保留上游提交历史、原作者署名和 MIT 许可证。原始工资计数器、基础界面及八套配色来自上游；此版本增加 macOS 菜单栏适配、下班倒计时、物品目标和中国调休自动同步。详细来源见 [致谢与来源](ATTRIBUTION.md)。

[下载最新版](https://github.com/quadratic-ZYH/xindong-macos/releases/latest) · [使用说明](docs/macos.md) · [更新日志](CHANGELOG.md) · [第三方组件](docs/third-party.md)

## 功能

- 默认只在后台和菜单栏运行，不占 Dock；点击金额展开完整面板，右键设置或退出。
- 今日累计收入精确到四位小数，状态栏同时显示距离下班的秒数。
- 1280 项、32 类趣味物品（含不同规格），参考价 ¥2.00–¥9498.10；攒够后随机换下一件。
- 物品进度只在展开面板显示；从启用时开始计薪，夜间和休息日暂停，退出后重启保留进度。
- 自动同步中国法定节假日与调休，离线使用内置数据/缓存，手动排班优先。
- 月薪、上下班时间、单双休、配色、透明度和登录启动均可设置。
- 八套配色与上游计薪方式保留；同一用户仅运行一份。

## 下载安装

当前 Release 提供 **Apple Silicon（M 系列）ARM64** 应用，内置 Python、Tk 和运行依赖。

> v1.4.0 本次本机构建包的运行库最低要求 **macOS 27.0**，实测环境为 macOS 27.0.1 / Apple M5。Intel Mac 和更早的 macOS 没有本次实测安装包；可自行从源码构建。

1. 下载 `SalaryMotivator-1.4.0-macos-arm64.dmg`。
2. 打开 DMG，将“薪动”拖入 `Applications`，再从“应用程序”启动。
3. 程序默认在菜单栏显示。单击金额展开面板，右键可进入设置或退出。

也提供 `SalaryMotivator-1.4.0-macos-arm64.zip`，解压后把 `薪动.app` 放入“应用程序”。升级时先退出旧版，再替换应用；工资设置与目标进度保存在用户目录，会继续保留。

应用使用本地临时签名，**未做 Apple Developer ID 签名或公证**。如果 macOS 提示无法验证开发者，请核对下载来源及校验值，并按 [Apple 官方打开应用说明](https://support.apple.com/en-gb/102445) 操作。

Release 同时提供 `SHA256SUMS.txt`、构建信息和源码压缩包。

## 如何使用

- 单击菜单栏金额：展开或收起面板；Esc 或切换应用也会收起。
- `⌘,`：打开工资、日历及外观设置；`⌘Q`：完全退出。
- 休息日显示“今日休息”，下班后显示“已下班”。
- 物品的“还需 N 计薪秒”仅计算工作时段，不包含夜间与假期等待时间。
- 物品价格为手工预设的趣味参考估值，不是实时报价，不发生真实购买。

详细排班、数据位置与构建步骤见 [macOS 使用说明](docs/macos.md)。

## 中国调休数据与隐私

数据来自 [NateScarlet/holiday-cn](https://github.com/NateScarlet/holiday-cn)，该项目根据国务院公告整理节假日和补班信息。内置 2025/2026 年数据，后台通过 HTTPS 更新；未公布年份不会猜测安排，会提示并暂按单双休计算。

规则优先级为 **手动日期 > 公布的国家安排 > 单双休规则**。单位或交易所的特殊排班请自行覆盖。

联网仅下载公开年度日历，不上传月薪、工作时间、目标进度或本机设置；本项目没有账号系统或遥测。

## 从源码运行

```sh
git clone https://github.com/quadratic-ZYH/xindong-macos.git
cd xindong-macos
brew install python-tk@3.14
python3.14 -m venv .venv
.venv/bin/python -m pip install -e . -r packaging/requirements-macos-build.txt
.venv/bin/python scripts/run.py
```

使用安装了 Tkinter 的 Python 版本。源码重建的系统兼容范围取决于 Python、Tk 和其他依赖的构建环境。

## 构建与检查

```sh
.venv/bin/python -m PyInstaller --noconfirm --distpath dist --workpath build/macos packaging/macos.spec
.venv/bin/python packaging/package_macos.py --app dist/薪动.app --output dist/release
.venv/bin/python tests/smoke_countdown.py
.venv/bin/python tests/smoke_goals.py
.venv/bin/python tests/smoke_holidays.py
```

本机桌面检查：`tests/smoke_core.py`、`tests/smoke_themes.py`、`tests/smoke_macos.py`。构建会收集第三方许可证，并根据实际 Mach-O 依赖计算最低 macOS 版本。

## 上游与许可证

- 基础项目：[WizzenH/xindong](https://github.com/WizzenH/xindong)，基线版本 v1.2.3，提交 `bf71f1a0fa27a4505db51fd7254cbc09582b37f3`。
- 调休数据：[NateScarlet/holiday-cn](https://github.com/NateScarlet/holiday-cn)。
- macOS 增强维护：[@quadratic-ZYH](https://github.com/quadratic-ZYH)。
- 代码采用 [MIT](LICENSE)；第三方组件各自保留许可证，见 [第三方说明](docs/third-party.md) 和 [third_party/licenses](third_party/licenses)。

上游的 Windows/Linux 构建脚本作为历史源码保留，此仓库当前只发布并验证 macOS ARM64 安装包。Windows/Linux 用户可查看 [上游项目](https://github.com/WizzenH/xindong)。
