"""Windowed app entry point with persistent local exception logging."""
import logging
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox

from salary_motivator.app import SalaryWidget
from salary_motivator.platform.single_instance import acquire_instance, release_instance


def main():
    log = Path.home() / "Library" / "Logs" / "SalaryMotivator.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=log, level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(message)s")
    if not acquire_instance():
        return
    app = None
    try:
        app = SalaryWidget()

        def callback_error(kind, value, traceback):
            logging.error("界面操作失败", exc_info=(kind, value, traceback))
            messagebox.showerror("薪动", "操作未完成，请重试。详情已写入本机日志。", parent=app.root)

        app.root.report_callback_exception = callback_error
        app.run()
    except Exception:
        logging.exception("薪动启动失败")
        if app is None:
            root = tk.Tk()
            root.withdraw()
        messagebox.showerror("薪动", f"启动失败，错误日志：\n{log}")
        if app is None:
            root.destroy()
        return 1
    finally:
        if app is not None and not app.closed:
            app.quit()
        release_instance()
    return 0


if __name__ == "__main__":
    sys.exit(main())
