const fs = require('fs');

// 1. Patch app.ts
let app = fs.readFileSync('src/stores/app.ts','utf8');
app = app.replace("const toastType = ref<'success' | 'error' | 'info'>('info')","const toastType = ref<'success' | 'error' | 'info' | 'warning'>('info')");
app = app.replace("function showToast(msg: string, type: 'success' | 'error' | 'info' = 'info')","function showToast(msg: string, type: 'success' | 'error' | 'info' | 'warning' = 'info')");
if(!app.includes('toasts')){
  app = app.replace('return { sidebarCollapsed',"const toasts = ref<Array<{id:number;msg:string;type:'success'|'error'|'info'|'warning'}>>([])\n  let toastId = 0\n  function showToastMulti(msg: string, type: 'success'|'error'|'info'|'warning' = 'info') {\n    const id = ++toastId\n    toasts.value.push({ id, msg, type })\n    setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, 3000)\n  }\n\n  return { sidebarCollapsed");
  app = app.replace('toggleSidebar, toggleDarkMode, setMode, showToast }','toggleSidebar, toggleDarkMode, setMode, showToast, showToastMulti, toasts }');
}
fs.writeFileSync('src/stores/app.ts', app, 'utf8');
console.log('[OK] app.ts');

// 2. ImageAnalyzer
let img = fs.readFileSync('src/components/common/ImageAnalyzer.vue','utf8');
img = img.replace(/\$refs\.fileInput\.click\(\)/g,'($refs.fileInput as HTMLInputElement).click()');
fs.writeFileSync('src/components/common/ImageAnalyzer.vue', img, 'utf8');
console.log('[OK] ImageAnalyzer.vue');

// 3. ChatView
let chat = fs.readFileSync('src/views/workspace/ChatView.vue','utf8');
chat = chat.replace("from '@//stores/appStore'","from '@/stores/app'");
chat = chat.replace("from '@//components/StatusBadge.vue'","from '@//components/common/StatusBadge.vue'");
fs.writeFileSync('src/views/workspace/ChatView.vue', chat, 'utf8');
console.log('[OK] ChatView.vue');

// 4. DashboardView router
let dash = fs.readFileSync('src/views/workspace/DashboardView.vue','utf8');
dash = dash.replace(/router\.push\(\/project\/\)/g,"router.push('/project/')");
dash = dash.replace(/\$router\.push\(\/project\/\)/g,"$router.push('/project/')");
fs.writeFileSync('src/views/workspace/DashboardView.vue', dash, 'utf8');
console.log('[OK] DashboardView.vue');

// 5. ProjectDetail
let proj = fs.readFileSync('src/views/workspace/ProjectDetail.vue','utf8');
proj = proj.replace(/const handleExport = async \(task\)/,'const handleExport = async (task: any)');
proj = proj.replace(/if \(typeof ElMessage !== 'undefined'\) ElMessage\.error\('导出失败: ' \+ e\.message\);[\s\S]*?else alert\('对出失h��: ' \+ e\.message\);/,"const errMsg = e instanceof Error ? e.message : String(e)\n      appStore.showToast('对出失h��: ' + errMsg, 'error')");
if(!proj.includes("from '@/stores/app'")){
  proj = proj.replace(/(import.*from.*@\/stores\/project['"])/,"$1\nimport { useAppStore } from '@/stores/app'");
}
if(!proj.includes('const appStore = useAppStore()')){
  proj = proj.replace(/const handleExport/,'const appStore = useAppStore()\nconst handleExport');
}
fs.writeFileSync('src/views/workspace/ProjectDetail.vue', proj, 'utf8');
console.log('[OK] ProjectDetail.vue');

// 6. exportPaper.d.ts
if(!fs.existsSync('src/utils')) fs.mkdirSync('src/utils',{recursive:true});
fs.writeFileSync('src/utils/exportPaper.d.ts','export function exportToWord(task: any): Promise<void>\n','utf8');
console.log('[OK] exportPaper.d.ts');

console.log('\nDone. Run: npm run build');
