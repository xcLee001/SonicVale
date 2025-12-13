<!-- src/components/WaveCellPro.vue -->
<template>
  <div class="wavecell">
    <div class="bar">
      <!-- 替换原来的按钮 -->
      <el-button :type="isPlaying ? 'danger' : 'success'" class="play-btn" :class="{ playing: isPlaying }" circle
        size="mid" @click="togglePlay">
        <template #icon>
          <el-icon :size="22">
            <VideoPause v-if="isPlaying" />
            <VideoPlay v-else />
          </el-icon>
        </template>
      </el-button>

      <!-- 下载按钮 -->
      <el-tooltip :content="ready ? '下载音频' : '暂无音频'" placement="top">
        <el-button class="download-btn" :class="{ 'is-disabled': !ready }" circle size="mid" 
          @click="downloadAudio" :disabled="!ready">
          <template #icon>
            <el-icon :size="18">
              <Download />
            </el-icon>
          </template>
        </el-button>
      </el-tooltip>


      <span class="lbl">速度</span>
      <el-slider v-model="rate" :min="0.5" :max="2.0" :step="0.1" class="slider" />

      <span class="lbl">音量</span>
      <el-slider v-model="vol2x" :min="0" :max="2.0" :step="0.01" class="slider" />

      <span class="lbl">添加间隔(s)</span>
      <el-input-number v-model="tailSilence" :min="0" :max="30" :step="0.1" size="small" />


      <!-- <el-switch v-model="regionMode" active-text="标注" inactive-text="浏览" /> -->
      <el-button size="small" @click="makeRegion" :disabled="hasRegion">删除区间选择</el-button>
      <!-- <el-button size="small" @click="loopRegion" :disabled="!hasRegion">循环区间</el-button> -->
      <el-button size="small" @click="clearRegion" :disabled="!hasRegion">清除区间</el-button>

      <el-button size="small" type="primary" @click="confirmProcess" :disabled="!ready">应用处理</el-button>
    </div>

    <div ref="container" class="wave" />
    <div ref="minimap" class="minimap" />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { VideoPlay, VideoPause, Download } from '@element-plus/icons-vue'
import WaveSurfer from 'wavesurfer.js'
import Regions from 'wavesurfer.js/dist/plugins/regions.esm.js'
import Minimap from 'wavesurfer.js/dist/plugins/minimap.esm.js'

const props = defineProps({
  src: { type: String, required: true },     // 建议传 file://；否则会尝试转换
  speed: { type: Number, default: 1.0 },     // 初始速度
  volume2x: { type: Number, default: 1.0 },  // 0~2.0（前端试听倍数）
  startMs: { type: Number, default: null },  // 初始选区
  endMs: { type: Number, default: null },
})

const emit = defineEmits([
  'request-stop-others', // (instance) 让父级停掉其它行
  'confirm',             // ({ speed, volume, start_ms, end_ms })
  'ready',
  'dispose',             // () 组件卸载时触发
  'ended',               // () 播放结束
])

const container = ref(null)
const minimap = ref(null)

let ws = null
let regionsPlugin = null
let minimapPlugin = null
const region = ref(null) // ← 关键：响应式

const isPlaying = ref(false)
const ready = ref(false)
const rate = ref(props.speed || 1.0)
const vol2x = ref(Math.max(0, Math.min(props.volume2x ?? 1.0, 1.0))) // 统一 0~1
const regionMode = ref(false)

const tailSilence = ref(0) // 默认 0 秒

const hasRegion = computed(() => !!region.value)

function toUrl(src) {
  if (!src) return ''
  if (/^https?:\/\//i.test(src) || /^file:\/\//i.test(src)) return src
  return window.native?.pathToFileUrl ? window.native.pathToFileUrl(src) : src
}

onMounted(async () => {
  ws = WaveSurfer.create({
    container: container.value,
    height: 64,
    normalize: true,
    autoScroll: true,
    autoCenter: true,
    barWidth: 2,
    waveColor: '#cfd6e4',
    progressColor: '#409EFF',
  })

  // v7：registerPlugin 获取实例
  regionsPlugin = ws.registerPlugin(Regions.create({ dragSelection: true }))
  minimapPlugin = ws.registerPlugin(Minimap.create({ container: minimap.value, height: 24 }))

  ws.on('ready', () => {
    ready.value = true
    ws.setPlaybackRate(rate.value)
    ws.setVolume(Math.max(0, Math.min(vol2x.value ?? 1.0, 1.0))) // 统一 0~1

    // 恢复初始区域
    if (props.startMs != null && props.endMs != null && props.endMs > props.startMs) {
      region.value = regionsPlugin.addRegion({
        start: props.startMs / 1000,
        end: props.endMs / 1000,
        drag: true,
        resize: true,
        color: 'rgba(64,158,255,0.15)',
      })
    }
    emit('ready', ws)
  })

  ws.on('play', () => {
    isPlaying.value = true
    emit('request-stop-others', ws)
  })
  ws.on('pause', () => { isPlaying.value = false })
  ws.on('finish', () => {
    isPlaying.value = false        // 确保状态同步
    console.log('播放结束，触发 ended 事件')
    emit('ended', { src: props.src })                 // 通知父组件
  })

  // 区域事件（v7：挂 regionsPlugin）
  regionsPlugin.on('region-created', r => { region.value = r })
  regionsPlugin.on('region-updated', r => { region.value = r })
  regionsPlugin.on('region-clicked', (r, e) => {
    e.stopPropagation()
    region.value = r
    if (regionMode.value) r.play({ loop: true })  // v7：用 play({ loop:true })
    else ws.play(r.start)
  })

  await ws.load(toUrl(props.src))
})

onBeforeUnmount(() => {
  try {
    emit('dispose', ws)
    ws && ws.destroy()
  }
  finally { ws = null; regionsPlugin = null; minimapPlugin = null; region.value = null }
})

// —— 实时预听：速度/音量 —— //
watch(rate, v => ws && ws.setPlaybackRate(v || 1.0))
watch(vol2x, v => ws && ws.setVolume(Math.max(0, Math.min(v ?? 1.0, 1.0))))

// 切换“标注/浏览”：开关拖拽建区
watch(regionMode, (on) => {
  if (regionsPlugin?.setOptions) regionsPlugin.setOptions({ dragSelection: !!on })

})

function togglePlay() {
  if (!ws) return
  isPlaying.value ? ws.pause() : ws.play()
}

function makeRegion() {
  if (!ws || region.value) return
  const dur = ws.getDuration() || 0
  const start = Math.max(0, (ws.getCurrentTime?.() || 0) - 0.25)
  const end = Math.min(dur, start + 1.5)
  region.value = regionsPlugin.addRegion({
    start, end,
    drag: true, resize: true,
    color: 'rgba(255,0,0,0.15)',
  })
}

function loopRegion() {
  if (region.value) region.value.play({ loop: true })
}

function clearRegion() {
  if (region.value) { region.value.remove(); region.value = null }
}

async function confirmProcess() {
  const start_ms = region.value ? Math.round(region.value.start * 1000) : null
  const end_ms = region.value ? Math.round(region.value.end * 1000) : null
  const current_ms = ws ? Math.round(ws.getCurrentTime() * 1000) : 0  // ✅ 新增
  await ElMessageBox.confirm('确认按当前试听参数处理该音频吗？（会生成新文件或覆盖，视后端实现）', '确认处理', { type: 'warning' })
  emit('confirm', {
    speed: Number(rate.value || 1.0),
    volume: Number(vol2x.value || 1.0),
    start_ms, end_ms,
    silence_sec: Number(tailSilence.value || 0),
    current_ms,
  })
}

// 下载音频
async function downloadAudio() {
  if (!props.src) {
    ElMessage.warning('暂无可下载的音频')
    return
  }

  try {
    // 解析源路径（支持 file:// 和普通路径）
    let sourcePath = props.src
    if (sourcePath.startsWith('file:///')) {
      // 解码 file:// URL 并提取路径
      sourcePath = decodeURI(sourcePath.replace('file:///', ''))
    } else if (sourcePath.startsWith('file://')) {
      sourcePath = decodeURI(sourcePath.replace('file://', ''))
    }
    
    // 去除可能存在的查询参数 (?v=xxx)
    sourcePath = sourcePath.split('?')[0]
    
    // 提取文件名作为默认保存名
    const fileName = sourcePath.split(/[\\/]/).pop() || 'audio.wav'
    
    // Electron 环境下使用原生保存对话框
    if (window.native?.saveFile && window.native?.writeFile) {
      const savePath = await window.native.saveFile({
        title: '保存音频文件',
        defaultPath: fileName,
        filters: [{ name: '音频文件', extensions: ['wav', 'mp3', 'flac', 'ogg'] }]
      })
      
      if (!savePath) {
        return // 用户取消
      }
      
      // 通过 fetch 获取音频数据
      const response = await fetch(toUrl(props.src))
      const arrayBuffer = await response.arrayBuffer()
      const uint8Array = new Uint8Array(arrayBuffer)
      
      // 使用 Electron 的 writeFile 方法直接写入文件
      const result = await window.native.writeFile(savePath, uint8Array)
      
      if (result.success) {
        ElMessage.success('音频下载成功')
      } else {
        ElMessage.error('写入文件失败: ' + (result.error || '未知错误'))
      }
    } else {
      // 非 Electron 环境，使用浏览器下载
      const response = await fetch(toUrl(props.src))
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      ElMessage.success('音频下载成功')
    }
  } catch (error) {
    console.error('下载音频失败:', error)
    ElMessage.error('下载音频失败: ' + (error.message || '未知错误'))
  }
}
</script>

<style scoped>
.wavecell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.lbl {
  font-size: 12px;
  color: #666;
  margin-left: 6px;
}

.slider {
  width: 140px;
}

.wave {
  width: 100%;
}

.minimap {
  width: 100%;
  opacity: .85;
}

/* 下载按钮样式 */
.download-btn {
  background: linear-gradient(135deg, #74b9ff 0%, #a29bfe 100%);
  border: none;
  color: #fff;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(116, 185, 255, 0.35);
}

.download-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(116, 185, 255, 0.5);
  background: linear-gradient(135deg, #a29bfe 0%, #74b9ff 100%);
}

.download-btn:active {
  transform: scale(0.95);
}

.download-btn .el-icon {
  color: #fff;
}

.download-btn.is-disabled {
  background: #c0c4cc;
  box-shadow: none;
  cursor: not-allowed;
}

.download-btn.is-disabled:hover {
  transform: none;
  background: #c0c4cc;
  box-shadow: none;
}
</style>
