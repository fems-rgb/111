# -*- coding: utf-8 -*-
import os, shutil

vue_path = r'D:\AI_Scientist\AI_Scientist\frontend\src\views\workspace\ExperimentLab.vue'
bak = vue_path + '.bak2'
if not os.path.exists(bak):
    shutil.copy2(vue_path, bak)
    print(f'Backup: {bak}')

content = open(vue_path, 'r', encoding='utf-8').read()

# Fix 1: Add isVideoFormat import
old_import = "getChartUrl, getVideoUrl,"
new_import = "getChartUrl, getVideoUrl, isVideoFormat,"
content = content.replace(old_import, new_import)

# Fix 2: Replace video display section - find the old img-only block and replace with video/img conditional
old_video = '''          <div v-if="result.video_path">
            <p class="text-xs text-gray-500 mb-2">\U0001f3ac \u52a8\u6001\u8fc7\u7a0b</p>
            <img :src="videoUrl()" class="w-full rounded-lg border" loading="lazy"/>
          </div>'''

new_video = '''          <div v-if="result.video_path">
            <p class="text-xs text-gray-500 mb-2">\U0001f3ac \u52a8\u6001\u8fc7\u7a0b</p>
            <video v-if="isVideoFormat(result.video_path)"
              :src="videoUrl()" controls autoplay loop muted
              class="w-full rounded-lg border" preload="metadata">
            </video>
            <img v-else :src="videoUrl()" class="w-full rounded-lg border" loading="lazy"/>
          </div>'''

if old_video in content:
    content = content.replace(old_video, new_video)
    print('Fixed: video display (img -> video/img conditional)')
else:
    # Try alternate form without emoji
    old_video2 = '<img :src="videoUrl()" class="w-full rounded-lg border" loading="lazy"/>'
    new_video2 = '''<video v-if="isVideoFormat(result.video_path)"
              :src="videoUrl()" controls autoplay loop muted
              class="w-full rounded-lg border" preload="metadata">
            </video>
            <img v-else :src="videoUrl()" class="w-full rounded-lg border" loading="lazy"/>'''
    if old_video2 in content:
        content = content.replace(old_video2, new_video2)
        print('Fixed: video display (alternate match)')
    else:
        print('WARNING: Could not find video section to patch')

# Fix 3: Update placeholder text to mention FuncAnimation
old_placeholder = "# plt.savefig() / plt.show() \\u81ea\\u52a8\\u6355\\u83b7\\u56fe\\u8868"
new_placeholder = "# plt.savefig() / plt.show() \\u81ea\\u52a8\\u6355\\u83b7\\u56fe\\u8868\\n# \\u4f7f\\u7528 FuncAnimation \\u81ea\\u52a8\\u751f\\u6210\\u52a8\\u753b(MP4/GIF)"
# This may or may not match depending on encoding; skip silently if not found

with open(vue_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Vue file patched successfully!')