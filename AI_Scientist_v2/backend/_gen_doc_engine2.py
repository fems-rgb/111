import pathlib, os

BASE = pathlib.Path('backend/app')

def w(rel, content):
    p = BASE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
    print(f'  wrote {p} ({len(content)} bytes)')

NL = chr(10)
TQ = chr(34) * 3
D = chr(36)
DD = D + D
BT3 = chr(96) * 3

print('Generating doc_engine.py ...')

lines = []
lines.append(TQ + 'Document Engine - orchestrates planning, writing, review, assembly' + TQ)
lines.append('import json, logging, asyncio')
lines.append('from typing import Optional')
lines.append('from app.agents.doc_planner import DocumentPlannerAgent, SectionWriterAgent')
lines.append('from app.contracts.document_template import get_template, DocumentTemplate')
lines.append('')
lines.append('logger = logging.getLogger(__name__)')
lines.append('')
lines.append('')
lines.append('class DocumentEngine:')
lines.append('    """Orchestrates the full document generation pipeline."""')
lines.append('')
lines.append('    def __init__(self, llm_client=None):')
lines.append('        self.llm_client = llm_client')
lines.append('        self.planner = DocumentPlannerAgent(llm_client=llm_client)')
lines.append('        self.writer = SectionWriterAgent(llm_client=llm_client)')
lines.append('')
lines.append('    async def generate_document(')
lines.append('        self,')
lines.append('        research_question: str,')
lines.append('        context: str,')
lines.append('        template_id: str = "nh_202619_track1",')
lines.append('        review_callback=None,')
lines.append('    ) -> dict:')
lines.append('        """Full pipeline: plan -> write sections -> assemble."""')
lines.append('        template = get_template(template_id)')
lines.append('        logger.info(f"[DocEngine] Starting generation with template {template_id}")')
lines.append('')
lines.append('        # Step 1: Plan')
lines.append('        plan_result = await self.planner.run(')
lines.append('            research_question=research_question,')
lines.append('            context=context,')
lines.append('            template_id=template_id,')
lines.append('        )')
lines.append('        if not plan_result.success:')
lines.append('            return {"success": False, "error": f"Planning failed: {plan_result.error}"}')
lines.append('')
lines.append('        plan_data = plan_result.output')
lines.append('        section_plans = plan_data.get("section_plans", [])')
lines.append('        hypothesis_list = plan_data.get("hypothesis_list", [])')
lines.append('        logger.info(f"[DocEngine] Plan complete: {len(section_plans)} sections")')
lines.append('')
lines.append('        # Step 2: Write sections in dependency order')
lines.append('        completed_sections = {}')
lines.append('        sorted_plans = sorted(section_plans, key=lambda x: x.get("writing_priority", 99))')
lines.append('')
lines.append('        for sp in sorted_plans:')
lines.append('            sid = sp.get("section_id", "")')
lines.append('            spec = None')
lines.append('            for s in template.sections:')
lines.append('                if s.section_id == sid:')
lines.append('                    spec = s')
lines.append('                    break')
lines.append('            if not spec:')
lines.append('                logger.warning(f"[DocEngine] No spec for section {sid}, skipping")')
lines.append('                continue')
lines.append('')
lines.append('            logger.info(f"[DocEngine] Writing section: {sid}")')
lines.append('            result = await self.writer.run(')
lines.append('                research_question=research_question,')
lines.append('                context=context,')
lines.append('                section_spec=spec,')
lines.append('                section_plan=sp,')
lines.append('                completed_sections=completed_sections,')
lines.append('                hypothesis_list=hypothesis_list,')
lines.append('            )')
lines.append('            if result.success:')
lines.append('                completed_sections[sid] = result.output')
lines.append('                logger.info(f"[DocEngine] Section {sid} written ({len(result.output)} chars)")')
lines.append('            else:')
lines.append('                logger.error(f"[DocEngine] Section {sid} failed: {result.error}")')
lines.append('                completed_sections[sid] = f"[SECTION FAILED: {result.error}]"')
lines.append('')
lines.append('        # Step 3: Assemble')
lines.append('        assembled = self._assemble(template, completed_sections)')
lines.append('        logger.info(f"[DocEngine] Assembly complete: {len(assembled)} chars")')
lines.append('')
lines.append('        return {')
lines.append('            "success": True,')
lines.append('            "document": assembled,')
lines.append('            "plan": plan_data,')
lines.append('            "sections": completed_sections,')
lines.append('        }')
lines.append('')
lines.append('    def _assemble(self, template: DocumentTemplate, sections: dict) -> str:')
lines.append('        """Assemble sections into final document."""')
lines.append('        parts = []')
lines.append('        for spec in template.sections:')
lines.append('            content = sections.get(spec.section_id, "[MISSING]")')
lines.append('            parts.append(content)')
lines.append('        return NL.join(parts)')

w('services/doc_engine.py', NL.join(lines))
print('doc_engine.py done')


# === __init__.py updates ===
print('Updating __init__.py files...')

agents_init = BASE / 'agents' / '__init__.py'
if agents_init.exists():
    existing = agents_init.read_text(encoding='utf-8')
else:
    existing = ''

new_imports = [
    'from app.agents.doc_planner import DocumentPlannerAgent, SectionWriterAgent',
]
added = []
for imp in new_imports:
    if imp not in existing:
        added.append(imp)

if added:
    updated = existing.rstrip() + NL + NL.join(added) + NL
    agents_init.write_text(updated, encoding='utf-8')
    print(f'  updated agents/__init__.py (+{len(added)} imports)')
else:
    print('  agents/__init__.py already up to date')

services_init = BASE / 'services' / '__init__.py'
if services_init.exists():
    existing = services_init.read_text(encoding='utf-8')
else:
    existing = ''

svc_import = 'from app.services.doc_engine import DocumentEngine'
if svc_import not in existing:
    updated = existing.rstrip() + NL + svc_import + NL
    services_init.write_text(updated, encoding='utf-8')
    print('  updated services/__init__.py')
else:
    print('  services/__init__.py already up to date')

print('All doc engine files generated successfully!')
