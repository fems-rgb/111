"""智研星瀚 - 125题批量结果汇总报告生成器"""
import json, argparse
from pathlib import Path
from datetime import datetime

def load_results(input_dir: str) -> list[dict]:
    results = []
    for f in sorted(Path(input_dir).glob("Q*.json")):
        with open(f, "r", encoding="utf-8") as fp:
            results.append(json.load(fp))
    return results

def generate_markdown(results: list[dict]) -> str:
    lines = [
        "# Science 125 前沿科学问题 — AI科研闭环输出报告", "",
        f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 总题数: {len(results)}",
        f"> 完成: {sum(1 for r in results if r.get('status')=='completed')}",
        f"> 失败: {sum(1 for r in results if r.get('status')=='failed')}", "", "---", ""
    ]
    for r in results:
        qid = r.get("question_id", "?")
        qtext = r.get("question_text", "")
        status = r.get("status", "unknown")
        output = r.get("final_output", "")
        lines.append(f"## {qid}: {qtext}")
        lines.append("")
        lines.append(f"**状态**: {'✅ 完成' if status == 'completed' else '❌ 失败'}")
        lines.append("")
        if status == "completed" and output:
            lines.append(output)
        elif status == "failed":
            lines.append(f"> ⚠️ 错误: {r.get('error_message', '未知错误')}")
        lines.extend(["", "---", ""])
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="batch_results")
    parser.add_argument("--output", default="batch_results/report_125.md")
    args = parser.parse_args()
    results = load_results(args.input)
    if not results:
        print(f"No results in {args.input}"); return
    md = generate_markdown(results)
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"Report generated: {out} ({len(results)} questions)")

if __name__ == "__main__":
    main()
