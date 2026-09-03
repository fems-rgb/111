<template>
  <div class="space-y-6 animate-fade-in">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold flex items-center gap-2">🧩 技能市场</h1>
      <button class="btn-primary text-sm">+ 注册新技能</button>
    </div>

    <!-- 技能分类筛选 -->
    <div class="flex gap-2 flex-wrap">
      <button v-for="cat in categories" :key="cat"
              @click="activeCategory = cat"
              :class="['px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
                       activeCategory === cat ? 'bg-primary-600 text-white' : 'bg-surface-100 text-surface-600 hover:bg-surface-200']">
        {{ cat }}
      </button>
    </div>

    <!-- 技能卡片网格 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="skill in filteredSkills" :key="skill.id"
           class="card hover:ring-2 ring-primary-200 transition-all cursor-pointer group">
        <div class="flex items-start justify-between mb-3">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
               :class="skill.color">{{ skill.icon }}</div>
          <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                :class="skill.installed ? 'bg-green-100 text-green-700' : 'bg-surface-100 text-surface-500'">
            {{ skill.installed ? '已安装' : '未安装' }}
          </span>
        </div>
        <h3 class="font-semibold mb-1">{{ skill.name }}</h3>
        <p class="text-sm text-surface-500 mb-3 line-clamp-2">{{ skill.description }}</p>
        <div class="flex items-center justify-between text-xs text-surface-400">
          <span>{{ skill.category }}</span>
          <span>v{{ skill.version }}</span>
        </div>
        <button v-if="!skill.installed"
                @click.stop="installSkill(skill.id)"
                class="mt-3 w-full btn-secondary text-sm py-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          安装技能
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const categories = ['全部', '数据分析', '文献检索', '实验设计', '代码生成', '可视化']
const activeCategory = ref('全部')

const skills = ref([
  { id: 'pdf-parser', name: 'PDF 论文解析器', icon: '📄', color: 'bg-blue-100', category: '文献检索', description: '自动提取 PDF 论文中的摘要、方法、实验结果等结构化信息', version: '1.2.0', installed: true },
  { id: 'stat-analyzer', name: '统计分析助手', icon: '📊', color: 'bg-purple-100', category: '数据分析', description: '支持 t检验/ANOVA/回归分析等常用统计方法，自动生成分析报告', version: '2.0.1', installed: true },
  { id: 'hypothesis-gen', name: '假设生成引擎', icon: '💡', color: 'bg-yellow-100', category: '实验设计', description: '基于文献综述自动生成可验证的科学假设，支持多领域模板', version: '1.0.0', installed: false },
  { id: 'code-scaffold', name: '实验代码脚手架', icon: '🐍', color: 'bg-green-100', category: '代码生成', description: '根据实验设计自动生成 Python/R 实验代码框架，含数据加载和评估指标', version: '1.5.0', installed: false },
  { id: 'chart-builder', name: '科研图表构建器', icon: '📈', color: 'bg-orange-100', category: '可视化', description: '一键生成符合期刊要求的矢量图表，支持 Nature/Science 样式模板', version: '1.1.0', installed: false },
  { id: 'citation-mgr', name: '引文管理器', icon: '📚', color: 'bg-red-100', category: '文献检索', description: '自动识别和管理参考文献，支持 BibTeX/EndNote 格式导出', version: '1.3.0', installed: true },
])

const filteredSkills = computed(() =>
  activeCategory.value === '全部' ? skills.value : skills.value.filter(s => s.category === activeCategory.value)
)

function installSkill(id: string) {
  const skill = skills.value.find(s => s.id === id)
  if (skill) skill.installed = true
}
</script>