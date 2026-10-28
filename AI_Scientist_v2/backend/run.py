"""智研星枢 v3.0 - 启动入口"""
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import uvicorn


def _disable_quickedit() -> None:
    """关掉 Windows 控制台的「快速编辑」模式。

    只要在黑窗口里点一下鼠标/选中文字，控制台就进入标记模式，进程再写 stdout
    会**永久阻塞**：日志先卡住，接着事件循环跟着卡死（接口全超时），Ctrl+C 也被
    控制台当成「复制」。禁用该模式后点窗口不会再冻结服务。
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
        mode = wintypes.DWORD()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return  # 输出重定向（非控制台）时直接跳过
        enable_extended_flags = 0x0080
        enable_quick_edit = 0x0040
        kernel32.SetConsoleMode(handle, (mode.value | enable_extended_flags) & ~enable_quick_edit)
    except Exception:
        pass


def main():
    _disable_quickedit()
    print(
        "\n"
        "    ╔══════════════════════════════════════════════╗\n"
        "    ║     🏛️  智研星枢 v3.0.0                       ║\n"
        "    ║     基于国产大模型的多智能体科研平台              ║\n"
        "    ║     http://localhost:8000                    ║\n"
        "    ╚══════════════════════════════════════════════╝\n"
        "    提示：Ctrl+C 停止服务；若卡住按两次 Ctrl+C 强退\n"
    )
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload="--reload" in sys.argv,
            log_level="info",
            # 有长任务在跑时，优雅关停最多等 5s，不让 Ctrl+C 干等
            timeout_graceful_shutdown=5,
        )
    except KeyboardInterrupt:
        # 优雅关停被拖住时，第二次 Ctrl+C 直接硬退，保证进程一定走得掉
        print("\n👋 已强制停止服务")
        os._exit(0)
    print("\n👋 服务已停止")


if __name__ == "__main__":
    main()
