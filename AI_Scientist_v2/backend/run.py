"""智研星枢 v3.0 - 启动入口"""
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import uvicorn


def main():
    print(
        "\n"
        "    ╔══════════════════════════════════════════════╗\n"
        "    ║     🏛️  智研星枢 v3.0.0                       ║\n"
        "    ║     基于国产大模型的多智能体科研平台              ║\n"
        "    ║     http://localhost:8000                    ║\n"
        "    ╚══════════════════════════════════════════════╝\n"
    )
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload="--reload" in sys.argv,
        log_level="info",
    )


if __name__ == "__main__":
    main()
