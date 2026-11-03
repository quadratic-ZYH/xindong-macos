# 薪动 1.4.0 · macOS 菜单栏版

针对 Apple Silicon Mac 构建，已在 Apple M5、16 GB、macOS 27.0.1 上验证。
基于 WizzenH/xindong 上游 1.2.3（bf71f1a0fa27a4505db51fd7254cbc09582b37f3）修改。

## 使用方式

- 双击 `薪动.app`。默认仅在后台运行，不显示桌面窗口和 Dock 图标。
- 右上角菜单栏显示 `¥28.1234 · 下班 9,503秒`，收入保留四位小数，倒计时逐秒更新。
- 单击菜单栏金额：在其下方展开完整收入面板；再点一次或按 Esc 收起。
- 切换到其他应用时收起收入面板；设置窗口打开时保留未保存的编辑。
- 面板里的“设置”或 `⌘,` 打开工资、日历和外观设置。
- 右键菜单栏金额：显示面板、设置、退出；`⌘Q` 也可退出。
- 从 Finder 再次打开正在后台运行的应用会显示已有面板，不会启动第二份。
- 登录启动默认关闭，可在“外观与启动”里启用并保存。
- 移动应用后，请关闭再开启登录启动，更新启动路径。

升级保留现有月薪、工作时间、配色和手动日期。首次使用默认月薪 10000 元仅为示例。

## 下班倒计时与趣味物品

倒计时按设置的下班时间计算，工作日上班前也会显示距离下班的真实秒数。
休息日显示“今日休息”，到达下班时间后显示“已下班”，不会显示负数。
节假日、周末补班和手动日期安排均会生效。

物品仅在展开面板显示，包含目标名称、参考价、已攒金额、剩余计薪秒数和进度。
物品库共有 **1280 项、32 个类别**（320 个基础品类，各含 4 种规格/包装/配置），
参考价范围 ¥2.00–¥9498.10，每项都低于 ¥10000，名称和编号均唯一。
完整清单见 `src/salary_motivator/assets/items.json`。

所有价格均为手工预设的趣味参考估值，不是商家实时报价，不会发生真实购买。
这些目标与实际工资结算、支出或购物车无关联。

- 首次运行 1.4.0 时从当前时刻开始，初始已攒金额为零，不使用当天此前累计收入。
- 按工作时间和计薪速度积累；夜间、休息日、法定假期不积累，补班日正常积累。
- 攒够后记为达成一个目标，随机换下一件，不连续重复上一件。下一个目标重新攒钱；
  两次刷新间越过达标时刻的微小余量会接入下一件，避免丢失计薪收入。
- “还需 N 计薪秒”指按当前月份计薪速度换算的工作秒数；休息时显示“暂停中”。
  它不包含夜间和休息日等待时间，因此与真实墙上时钟的倒计时不同。
- 重启保留目标和进度，并补算关闭期间的计薪时段；跨月时按各月工作日数计算。
- 进度每 5 秒保存，达标及正常退出时立即保存。只保存当前目标、余额、数量和时间。

## 中国节假日与调休

“自动同步中国法定节假日与调休”默认开启。
数据使用根据国务院公告整理的 [NateScarlet/holiday-cn](https://github.com/NateScarlet/holiday-cn)，
通过 GitHub Raw 下载，失败时尝试项目公布的 jsDelivr 地址；使用 HTTPS 验证证书。
每份数据保留其国务院公告链接，并在使用前检查年份、日期和班休标记。

- 启动后在后台更新，以后每 24 小时检查一次；失败后 30 分钟重试，不阻塞界面。
- 同时检查当前年份和下一年份，处理下一年公告影响前一年 12 月的情况。
- 查看其他年份时也会更新相应数据；“更新调休”可立即重试。
- 内置 2025、2026 年数据，成功更新后写入本机缓存；断网可继续计算。
- 本次检查时 2027 年尚无完整已公布数据；应用会显示提示，暂按单双休计算，不虚构调休。
- 日期旁 `·` 表示国家安排，`*` 表示手动修改。
- 规则优先级：手动日期 > 公布的国家安排 > 单双休规则。
- “清除本月手动修改”恢复自动规则；关闭自动调休后，仅按单双休和手动日期计算。

仅下载公开年度日历，不上传工资、工作时间或本机设置。
交易所或单位的特殊排班请用手动日期覆盖。

## 本机文件

- 工资设置：`~/Library/Application Support/salary-motivator/settings.json`
- 调休缓存：`~/Library/Application Support/salary-motivator/holidays/`
- 物品进度：`~/Library/Application Support/salary-motivator/goals.json`
- 异常日志：`~/Library/Logs/SalaryMotivator.log`
- 登录启动：`~/Library/LaunchAgents/io.github.wizzenh.xindong.plist`

## 源码运行和重建

在解压后的 xindong 项目根目录执行：

```sh
brew install python-tk@3.14
python3.14 -m venv .venv
.venv/bin/python -m pip install -e . -r packaging/requirements-macos-build.txt
.venv/bin/python scripts/run.py
```

打包：

```sh
.venv/bin/python -m PyInstaller --noconfirm --distpath dist --workpath build/macos packaging/macos.spec
```

结果为 `dist/薪动.app`，自带 Python 3.14.10、Tcl/Tk 9.1.0、PyObjC 13.0 和 CA 证书。
ARM64 本地构建带临时签名，未做开发者公证；本次本地发布包的运行库最低要求 macOS 27.0，其他 Mac 型号和 macOS 版本未实测。

## 检查

```sh
.venv/bin/python tests/smoke_core.py
.venv/bin/python tests/smoke_themes.py
.venv/bin/python tests/smoke_macos.py
.venv/bin/python tests/smoke_holidays.py
.venv/bin/python tests/smoke_countdown.py
.venv/bin/python tests/smoke_goals.py
```

覆盖后台启动、无 Dock、菜单栏收入与倒计时、面板开关/定位/收起、设置保存、八套配色、
计薪边界、法定假期/周末补班、手动覆盖、跨年公告、损坏数据与离线缓存。
另已执行真实 HTTPS 日历刷新检查。登录启动检查包括配置与命令，未注销或重启实测。
目标检查还覆盖全量价格约束、自动换物品、秒数取整、重启持久化、系统时钟回退及跨月计薪。

项目代码采用 MIT 许可证；调休数据许可证保留在 `src/salary_motivator/assets/holidays/LICENSE.txt`。
