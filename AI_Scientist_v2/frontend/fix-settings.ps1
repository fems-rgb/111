$path = "D:\AI_Scientist\AI_Scientist\frontend\src\views\settings\SettingsView.vue"
$enc = New-Object System.Text.UTF8Encoding $false
$c = [System.IO.File]::ReadAllText($path, $enc)

# 1. 确保 watch 导入
if ($c -notmatch "watch.*from 'vue'") {
    $c = $c.Replace("import { ref, onMounted } from 'vue'", "import { ref, onMounted, watch } from 'vue'")
}

# 2. 注入 script 逻辑
$s = "`n// ===== 外观设置 =====`nconst fontSize = ref(parseInt(localStorage.getItem('fontSize') || '14'))`nconst darkMode = ref(localStorage.getItem('darkMode') || 'light')`nconst compactMode = ref(localStorage.getItem('compactMode') === 'true')`nconst mode = ref(darkMode.value)`nconst modeOptions = [{ value: 'light', label: '\u2600\uFE0F \u6D45\u8272' }, { value: 'dark', label: '\uD83C\uDF19 \u6DF1\u8272' }, { value: 'auto', label: '\uD83D\uDCBB \u8DDF\u968F\u7CFB\u7EDF' }]`nconst applyDarkMode = (m) => { if (m === 'dark') document.documentElement.classList.add('dark'); else document.documentElement.classList.remove('dark') }`nwatch(fontSize, (v) => { document.documentElement.style.setProperty('--font-size-base', v + 'px'); localStorage.setItem('fontSize', String(v)) })`nwatch(mode, (v) => { darkMode.value = v; localStorage.setItem('darkMode', v); applyDarkMode(v) })`nwatch(compactMode, (v) => { localStorage.setItem('compactMode', String(v)); document.documentElement.classList.toggle('compact', v) })`n"
if ($c -notmatch "const fontSize = ref") {
    $anchor = "// ===== 个人资料"
    if ($c.Contains($anchor)) { $c = $c.Replace($anchor, $s + "`n" + $anchor) }
    else {
        $anchor2 = "<script setup>"
        $c = $c.Replace($anchor2, $anchor2 + $s)
    }
}

# 3. 注入 template UI
$t = "`n      <!-- 外观主题 -->`n      <div class=`"p-6 bg-white rounded-lg shadow-sm mb-6`">`n        <h2 class=`"text-lg font-semibold mb-4 flex items-center`"><span class=`"mr-2`">🎨</span> 外观主题</h2>`n        <div class=`"mb-5`"><label class=`"block text-sm font-medium mb-2`">字体大小</label><input type=`"range`" v-model=`"fontSize`" min=`"12`" max=`"20`" class=`"w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer`" /><div class=`"flex justify-between text-xs text-gray-500 mt-1`"><span>12px</span><span>{{ fontSize }}px</span><span>20px</span></div></div>`n        <div class=`"mb-5`"><label class=`"block text-sm font-medium mb-2`">深色模式</label><div class=`"flex space-x-4`"><button v-for=`"item in modeOptions`" :key=`"item.value`" @click=`"mode = item.value`" :class=`"['px-4 py-2 rounded-md text-sm font-medium transition-colors', mode === item.value ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200']`">{{ item.label }}</button></div></div>`n        <div class=`"mb-5`"><label class=`"block text-sm font-medium mb-2`">紧凑模式 <span class=`"ml-2 text-xs text-gray-500`">(减小间距)</span></label><div class=`"flex items-center`"><input type=`"checkbox`" v-model=`"compactMode`" class=`"h-4 w-4 text-blue-600 rounded focus:ring-blue-500`" /><span class=`"ml-2 text-sm text-gray-700`">启用紧凑布局</span></div></div>`n        <p class=`"text-xs text-gray-400 pt-2`">💡 以上设置即时生效，自动保存到本地</p>`n      </div>`n"
if ($c -notmatch "外观主题") {
    $ta = "<!-- 个人资料 -->"
    if ($c.Contains($ta)) { $c = $c.Replace($ta, $t + "`n      " + $ta) }
    else {
        $ta2 = "<template>"
        $c = $c.Replace($ta2, $ta2 + $t)
    }
}

[System.IO.File]::WriteAllText($path, $c, $enc)
Write-Host "Done" -ForegroundColor Green
