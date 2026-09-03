import asyncio, sys
sys.path.insert(0, '.')
from app.agents.doc_orchestrator import DocumentOrchestrator

async def test():
    engine = DocumentOrchestrator(template_id='nh_202619_track1')
    result = await engine.generate(
        research_question='基于FAST脉冲星计时阵列的纳赫兹引力波背景探测新方法',
        context='',
    )
    doc = result['document']
    meta = result['metadata']
    with open('test_output.md', 'w', encoding='utf-8') as f:
        f.write(doc)
    print(f'OK: {meta["total_chars"]} chars, {meta["section_count"]} sections, {meta["elapsed_seconds"]}s')
    print(f'Tokens: {meta["total_tokens"]}, Cost: {meta["total_cost"]:.4f} yuan')

asyncio.run(test())
