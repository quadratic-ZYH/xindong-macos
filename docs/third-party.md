# 来源与第三方组件

## 项目与数据署名

本项目基于 **[WizzenH/xindong](https://github.com/WizzenH/xindong)** 派生，保留原作者 WizzenH 的 MIT 版权声明和提交历史；此仓库的 macOS 增强由 quadratic-ZYH 维护。详见 [ATTRIBUTION.md](../ATTRIBUTION.md)。

中国节假日与调休数据来自 **[NateScarlet/holiday-cn](https://github.com/NateScarlet/holiday-cn)**（MIT），许可证位于 `src/salary_motivator/assets/holidays/LICENSE.txt`。

1280 项物品数据为本派生版本手工整理的趣味参考估值，不是任何电商平台的实时报价。

## macOS v1.4.0 本机构建

应用内 `Contents/Resources/licenses/` 保存本项目、来源说明和以下组件的许可证。
源码中也保留在 [third_party/licenses](../third_party/licenses)。

| 组件 | 本次构建版本 | 许可证/来源 |
| --- | --- | --- |
| CPython | 3.14.10 | Python / PSF 及其原有第三方声明；`CPython-LICENSE.txt` |
| Tcl/Tk | 9.1.0 | Tcl/Tk 原始许可；`Tcl-Tk-license.terms` |
| PyObjC Cocoa / Core | 13.0 | MIT；`PyObjC-LICENSE.txt`；使用系统 libffi 和 Cocoa 框架 |
| certifi / CA bundle | 2026.10.23 | Mozilla Public License 2.0 相关声明；`certifi-LICENSE.txt`；证书来源链接在该文件中 |
| PyInstaller bootloader | 6.22.3 | GPL 及 bootloader 分发例外；`PyInstaller-COPYING.txt` |
| OpenSSL | 4.1.0 | Apache 2.0；`OpenSSL-LICENSE.txt` |
| mpdecimal | 4.0.1 | BSD；`mpdecimal-COPYRIGHT.txt` |
| liblzma / XZ | 5.8.4 | liblzma 为 0BSD；`XZ-COPYING.txt`、`XZ-0BSD.txt` |
| Zstandard | 1.5.7 | BSD 分发选项；`Zstandard-LICENSE.txt` |
| LibTomMath | 1.3.0 | MIT / Unlicense 原始双许可文本；`LibTomMath-LICENSE.txt` |

macOS 自带系统库和框架不复制到应用内。Pillow 仅用于构建图标，不作为应用运行依赖。
构建规范会排除 macOS 不使用的 Linux/X11 库。重新构建时依赖版本可能变化，请核对构建环境和随包许可证。

## 上游 Windows/Linux 历史脚本

保留的 Windows 包构建脚本使用 CPython 3.13.12 x64、Python 官方 Tcl/Tk 组件、Visual C++ runtime 和 NSIS；原上游发行包保留各自许可证。
Linux 历史包依赖系统提供的 Python、Tk、GTK、PyGObject 和 AppIndicator。此仓库本次不构建或发布这些平台安装包。
