import os
# 看前端 package.json 的启动脚本
p = "frontend/package.json"
if os.path.exists(p):
    print(open(p, encoding="utf-8").read()[:800])
else:
    print("frontend/package.json 不存在！")
