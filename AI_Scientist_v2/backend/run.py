import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
"""智研星枢 v3.0 - 启动入口"""
import uvicorn
import sys

def main():
    print("""
    ╔══════════════════════════════════════════════╗
    ║     🏛️  智研星枢 v3.0.0                       ║
    ║     基于国产大模型的多智能体科研平台              ║
    ║     http://localhost:8000                    ║
    ╚══════════════════════════════════════════════╝
    """)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000,
                reload="--reload" in sys.argv, log_level="info")

if __name__ == "__main__":
    main()