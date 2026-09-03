const fs = require('fs');
const path = require('path');

// 1. 扫描所有中文文案
const entries = [];
function walk(dir) {
  for (const f of fs.readdirSync(dir)) {
    const p = path.join(dir, f);
    if (fs.statSync(p).isDirectory()) {
      if (f === 'node_modules' || f === '.git') continue;
      walk(p);
    } else if (/\.(vue|ts)$/.test(f) && !f.endsWith('.d.ts')) {
      const content = fs.readFileSync(p, 'utf8');
      const rel = path.relative('src', p).replace(/\\/g, '/');
      const lines = content.split('\n');
      lines.forEach((line, idx) => {
        const trimmed = line.trim();
        if (trimmed.startsWith('//') || trimmed.startsWith('*') || trimmed.startsWith('/*')) return;
        const matches = line.match(/[\u4e00-\u9fff][\u4e00-\u9fff\w\s\d%()（）:：!！?？,，.。、;；"“”‘’\-]*/g);
        if (matches) {
          matches.forEach(m => {
            const text = m.trim();
            if (text.length >= 2) entries.push({ file: rel, line: idx + 1, text });
          });
        }
      });
    }
  }
}
walk('src');

// 2. 去重并按文件分组生成 key
const uniqueMap = new Map();
entries.forEach(e => {
  if (!uniqueMap.has(e.text)) uniqueMap.set(e.text, e);
});

// 3. 按模块分组的 key 命名策略
const moduleMap = {
  'components/common/': 'common',
  'components/layout/': 'layout',
  'views/workspace/ChatView': 'chat',
  'views/workspace/DashboardView': 'dashboard',
  'views/workspace/ProjectDetail': 'project',
  'views/admin/': 'admin',
  'composables/': 'composable',
  'stores/': 'store',
  'utils/': 'util'
};

function getModule(file) {
  for (const [prefix, mod] of Object.entries(moduleMap)) {
    if (file.includes(prefix)) return mod;
  }
  return 'misc';
}

function toKey(text, mod) {
  // 用拼音首字母或前几个字符作为 key 后缀
  const clean = text.replace(/[^\u4e00-\u9fffa-zA-Z0-9]/g, '').slice(0, 8);
  return `${mod}.${clean}`;
}

// 4. 构建 zh-CN.json
const zhCN = {};
const usedKeys = new Set();
for (const [text, entry] of uniqueMap) {
  const mod = getModule(entry.file);
  let key = toKey(text, mod);
  // 处理重复 key
  let suffix = 1;
  while (usedKeys.has(key)) {
    key = `${toKey(text, mod)}_${suffix++}`;
  }
  usedKeys.add(key);

  const parts = key.split('.');
  if (!zhCN[parts[0]]) zhCN[parts[0]] = {};
  zhCN[parts[0]][parts.slice(1).join('.')] = text;
}

// 5. 写入文件
const outDir = 'src/i18n';
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, 'zh-CN.json'), JSON.stringify(zhCN, null, 2), 'utf8');

console.log(`? Generated ${Object.keys(zhCN).length} modules, ${usedKeys.size} entries`);
console.log(`?? Saved to src/i18n/zh-CN.json`);
