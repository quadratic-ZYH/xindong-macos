# 来源、致谢与改动边界

## 基础项目：WizzenH/xindong

本仓库是 [WizzenH/xindong](https://github.com/WizzenH/xindong) 的 **fork / 派生版本**，不是从零独立实现。
基于 v1.2.3（提交 `bf71f1a0fa27a4505db51fd7254cbc09582b37f3`）开发，原作者为 WizzenH，原始 Git 提交历史保留。

沿用的主要内容：工资折算与按时钟计薪逻辑、桌面卡片与设置界面、八套配色、Windows/Linux 平台实现，以及原有文档、图标和检查代码。

此派生版本新增：

- Apple Silicon macOS 适配、原生菜单栏实时金额、后台运行、面板定位和快捷键。
- 距离下班的秒级倒计时。
- 1280 项趣味参考物品、计薪秒数估算、自动随机换目标与进度持久化。
- 中国节假日/调休自动更新、缓存及离线回退。
- macOS 应用、DMG/ZIP 分发、第三方许可证归档和发布说明。

原项目的 MIT 许可证和 `Copyright (c) 2026 WizzenH` 保留在根目录 [LICENSE](LICENSE)。

## 数据来源：NateScarlet/holiday-cn

中国节假日和调休数据采用 [NateScarlet/holiday-cn](https://github.com/NateScarlet/holiday-cn)。
该项目根据国务院公告生成年度 JSON 数据。本应用读取并校验这些数据，同时保留各年 `papers` 公告链接。

数据原许可证保留在 `src/salary_motivator/assets/holidays/LICENSE.txt`，随源码和应用一起分发。
物品库为本派生版本整理的娱乐性参考估值，未声称引用任何电商平台实时报价。

## 维护者与其他组件

macOS 增强版由 [quadratic-ZYH](https://github.com/quadratic-ZYH) 维护。
CPython、Tcl/Tk、PyObjC、certifi、PyInstaller 及动态依赖仍按各自许可证分发，详见 [第三方组件](docs/third-party.md)。
