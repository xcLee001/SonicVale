<template>
  <div>
    <div class="page-header">
      <h2>音色管理</h2>
      <div class="actions">
        <el-select v-model="selectedTTS" placeholder="选择 TTS 引擎" class="tts-select" @change="loadVoices">
          <el-option v-for="t in ttsProviders" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button type="primary" :disabled="!selectedTTS" @click="openDialog()">新增音色</el-button>
        <el-button type="success" plain :disabled="!selectedTTS || selectedCount === 0" @click="handleExportSelected">导出音色库（选中）</el-button>
        <el-popconfirm
          title="确认删除选中的音色？"
          confirm-button-text="确定"
          cancel-button-text="取消"
          @confirm="handleBatchDelete"
        >
          <template #reference>
            <el-button type="danger" plain :disabled="!selectedTTS || selectedCount === 0">批量删除（选中）</el-button>
          </template>
        </el-popconfirm>
        <el-button type="warning" :disabled="!selectedTTS" @click="handleImport">导入音色库</el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-select
        ref="filterSelectRef"
        v-model="filterTags"
        multiple
        filterable
        clearable
        collapse-tags
        collapse-tags-tooltip
        placeholder="标签筛选"
        class="filter-tags"
        @change="handleFilterTagChange"
      >
        <el-option v-for="tag in allTags" :key="tag" :label="tag" :value="tag" />
      </el-select>
      <el-input v-model="searchName" placeholder="按名称搜索" clearable class="filter-search" />
      <el-button plain :disabled="!searchName && !filterTags.length" @click="resetFilters">重置筛选</el-button>
      <div class="filter-result">共 {{ filteredVoices.length }} 条</div>
    </div>

    <el-table
      :data="filteredVoices"
      ref="voiceTableRef"
      border
      stripe
      highlight-current-row
      class="voice-table"
      :header-cell-style="headerCellStyle"
      :cell-style="cellStyle"
      row-key="id"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="48" align="center" />
      <el-table-column label="#" width="80" align="center">
        <template #default="{ $index }">{{ $index + 1 }}</template>
      </el-table-column>

      <el-table-column prop="name" label="名称" min-width="180" />

      <el-table-column label="播放" width="160" align="center">
        <template #default="{ row }">
          <el-button
            size="small"
            :type="row.reference_path ? 'primary' : 'default'"
            :plain="!row.reference_path"
            :disabled="!row.reference_path"
            @click="togglePlay(row.reference_path)"
          >
            <el-icon style="margin-right:4px;">
              <Headset />
            </el-icon>
            {{ isPlaying && currentPath === row.reference_path ? '暂停' : '播放' }}
          </el-button>
        </template>
      </el-table-column>

      <!-- 描述改为 tag 展示 -->
      <el-table-column prop="description" label="标签" min-width="220">
        <template #default="{ row }">
          <div class="tags-wrap">
            <el-tag
              v-for="(tag, index) in (row.description ? row.description.split(',') : [])"
              :key="index"
              type="info"
              effect="plain"
              style="margin-right: 6px;"
            >
              {{ tag }}
            </el-tag>
            <span v-if="!row.description">—</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="参考音频/路径" min-width="200" align="center">
        <template #default="{ row }">
          <el-tooltip :content="row.reference_path ? row.reference_path : '未设置参考音频'" placement="top">
            <span class="path-ellipsis">{{ row.reference_path || '（未设置）' }}</span>
          </el-tooltip>
        </template>
      </el-table-column>

      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="更新时间" width="180">
        <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
      </el-table-column>

      <el-table-column label="操作" width="320" fixed="right" align="center">
  <template #default="{ row }">
    <div class="flex justify-center gap-2">
      <el-button 
        type="primary" 
        size="small" 
        plain 
        @click="openDialog(row)">
        编辑
      </el-button>
      <el-button 
        type="success" 
        size="small" 
        plain
        @click="openCopyDialog(row)">
        复制
      </el-button>
      <el-button 
        type="warning" 
        size="small" 
        plain
        :disabled="!row.reference_path"
        @click="openAudioEditor(row)">
        音频编辑
      </el-button>
      <el-popconfirm
        title="确认删除该音色？"
        confirm-button-text="确定"
        cancel-button-text="取消"
        @confirm="handleDelete(row.id)"
      >
        <template #reference>
          <el-button 
            type="danger" 
            size="small" 
            plain>
            删除
          </el-button>
        </template>
      </el-popconfirm>
    </div>
  </template>
</el-table-column>

    </el-table>

    <!-- 弹窗：新增/编辑 -->
    <el-dialog :title="form.id ? '编辑音色' : '新增音色'" v-model="dialogVisible" width="720px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入音色名称" />
        </el-form-item>

        <!-- 描述改为标签输入 -->
        <el-form-item label="标签" class="tag-item">
  <div class="tag-hint">可直接选择下方标签，也可以输入自定义标签后回车添加</div>
  <el-select
    ref="tagSelectRef"
    v-model="form.tags"
    multiple
    filterable
    allow-create
    default-first-option
    placeholder="输入或选择标签（回车添加）"
    style="width: 100%;"
    @change="handleTagChange"
  >
    <el-option
      v-for="opt in defaultTags"
      :key="opt"
      :label="opt"
      :value="opt"
    />
  </el-select>
</el-form-item>



        <el-form-item label="参考音频">
          <div class="pick-line">
            <el-input v-model="form.reference_path" placeholder="请选择本地音频文件" readonly style="width:420px" />
            <el-button @click="pickLocalAudioForBase" style="margin-left:8px">选择文件</el-button>
            <el-button v-if="form.reference_path" type="danger" link @click="clearReferencePath">清除</el-button>
          </div>

          <div class="preview" v-if="form.reference_path">
            <el-alert title="已选择本地音频文件" type="success" :closable="false" show-icon class="mb8" />
            <div class="path-text">{{ form.reference_path }}</div>
            <el-button type="primary" size="small" @click="togglePlay(form.reference_path)">
              {{ isPlaying && currentPath === form.reference_path ? '暂停' : '播放' }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗：音频编辑 -->
    <el-dialog title="音频编辑" v-model="audioEditorVisible" width="900px" :close-on-click-modal="false">
      <div class="audio-editor-info" v-if="editingVoice">
        <span class="audio-editor-label">音色名称：</span>
        <span class="audio-editor-value">{{ editingVoice.name }}</span>
      </div>
      <div class="wave-editor-wrap" v-if="editingVoice?.reference_path && waveEditorKey">
        <WaveCellPro
          :key="waveEditorKey"
          :src="editingVoice.reference_path"
          :speed="1.0"
          :volume2x="1.0"
          @confirm="handleWaveConfirm"
          @ready="handleWaveReady"
        />
      </div>
      <template #footer>
        <el-button @click="audioEditorVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗：导入音色库 -->
    <el-dialog title="导入音色库" v-model="importDialogVisible" width="600px">
      <el-form :model="importForm" label-width="120px">
        <el-form-item label="音色库文件">
          <div class="pick-line">
            <el-input v-model="importForm.zipPath" placeholder="请选择音色库zip文件" readonly style="flex:1" />
            <el-button @click="pickImportZip" style="margin-left:8px">选择文件</el-button>
          </div>
        </el-form-item>
        <el-form-item label="音色保存目录">
          <div class="pick-line">
            <el-input v-model="importForm.targetDir" placeholder="音色文件保存目录" style="flex:1" />
            <el-button @click="pickImportDir" style="margin-left:8px">选择目录</el-button>
          </div>
          <div class="form-hint">导入的音色文件将保存到此目录</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!importForm.zipPath || !importForm.targetDir" @click="confirmImport">确认导入</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗：复制音色 -->
    <el-dialog title="复制音色" v-model="copyDialogVisible" width="600px">
      <el-form :model="copyForm" :rules="copyRules" ref="copyFormRef" label-width="120px">
        <el-form-item label="原音色名称">
          <el-input :value="copyForm.sourceName" disabled />
        </el-form-item>
        <el-form-item label="新音色名称" prop="newName">
          <el-input v-model="copyForm.newName" placeholder="请输入新音色名称" />
        </el-form-item>
        <el-form-item label="保存目录">
          <div class="pick-line">
            <el-input v-model="copyForm.targetDir" placeholder="留空则保存到原音色同目录" style="flex:1" />
            <el-button @click="pickCopyTargetDir" style="margin-left:8px">选择目录</el-button>
          </div>
          <div class="form-hint">留空则将新音色文件保存到原音色所在目录</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="copyDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!copyForm.newName" @click="confirmCopy">确认复制</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Headset } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { createVoice, fetchVoicesByTTS, updateVoice, deleteVoice, exportVoices, importVoices, processVoiceAudio, copyVoice } from '../api/voice'
import { fetchTTSProviders } from '../api/provider'
import WaveCellPro from '../components/WaveCellPro.vue'


const defaultTags = ref([
  '男',
  '女',
  '小孩',
  '青年',
  '中年',
  '老年'
])

// @ts-ignore - 由 preload 暴露
const native = window.native

const ttsProviders = ref([])
const selectedTTS = ref(null)
const voices = ref([])
const voiceTableRef = ref(null)
const selectedRows = ref([])
const selectedIds = computed(() => (selectedRows.value || []).map(v => v?.id).filter(v => v !== null && v !== undefined))
const selectedCount = computed(() => selectedIds.value.length)

const filterTags = ref([])
const searchName = ref('')
const filterSelectRef = ref(null)

const allTags = computed(() => {
  const set = new Set()
  defaultTags.value.forEach(t => t && set.add(t))
  voices.value.forEach(v => {
    const tags = v.description ? v.description.split(',') : []
    tags.map(t => t.trim()).filter(Boolean).forEach(t => set.add(t))
  })
  return Array.from(set)
})

const filteredVoices = computed(() => {
  const name = searchName.value.trim()
  const nameLower = name.toLowerCase()
  return voices.value.filter(v => {
    const voiceName = (v.name || '').toString()
    const matchName = !name || voiceName.toLowerCase().includes(nameLower)
    if (!filterTags.value.length) return matchName
    const tags = v.description ? v.description.split(',').map(t => t.trim()).filter(Boolean) : []
    const matchTags = filterTags.value.every(ft => tags.includes(ft))
    return matchName && matchTags
  })
})

function handleSelectionChange(rows) {
  selectedRows.value = rows || []
}

function formatDateTime(value) {
  if (!value) return '—'
  const d = dayjs(value)
  if (!d.isValid()) return String(value)
  return d.format('YYYY-MM-DD HH:mm:ss')
}

async function clearTableSelection() {
  await nextTick()
  voiceTableRef.value?.clearSelection?.()
  selectedRows.value = []
}

// ====== 音频播放控制 ======
const audioPlayer = new Audio()
const isPlaying = ref(false)
const currentPath = ref(null)

function togglePlay(absPath) {
  if (!absPath) return
  const url = toFileUrl(absPath)
  if (!url) {
    ElMessage.error('无法播放该音频文件')
    return
  }

  if (currentPath.value === absPath) {
    if (isPlaying.value) {
      audioPlayer.pause()
    } else {
      audioPlayer.play().catch(() => ElMessage.error('无法播放该音频文件'))
    }
    return
  }

  audioPlayer.pause()
  audioPlayer.src = url
  audioPlayer.currentTime = 0
  currentPath.value = absPath
  audioPlayer.play().catch(() => ElMessage.error('无法播放该音频文件'))
}

audioPlayer.addEventListener('play', () => { isPlaying.value = true })
audioPlayer.addEventListener('pause', () => { isPlaying.value = false })
audioPlayer.addEventListener('ended', () => {
  isPlaying.value = false
  currentPath.value = null
})

const dialogVisible = ref(false)
watch(dialogVisible, v => { 
  if (!v) {
    audioPlayer.pause()
  }
})

// ====== 独立音频编辑弹窗 ======
const audioEditorVisible = ref(false)
const editingVoice = ref(null)

watch(audioEditorVisible, v => {
  if (!v) {
    audioPlayer.pause()
    waveEditorKey.value = null
    editingVoice.value = null
  }
})

function openAudioEditor(row) {
  if (!row.reference_path) {
    ElMessage.warning('该音色没有参考音频')
    return
  }
  audioPlayer.pause()
  editingVoice.value = row
  waveEditorKey.value = Date.now()
  audioEditorVisible.value = true
}

// 表单
const formRef = ref(null)
const form = ref({
  id: null,
  name: '',
  tags: [],
  reference_path: '',
  tts_provider_id: null
})

const rules = {
  name: [{ required: true, message: '请输入音色名称', trigger: 'blur' }]
}

// 表格样式
const headerCellStyle = () => ({
  background: 'var(--el-fill-color-light)',
  color: 'var(--el-text-color-primary)',
  fontWeight: 600
})
const cellStyle = () => ({ padding: '10px 12px' })

// 加载 TTS
const loadTTS = async () => {
  ttsProviders.value = await fetchTTSProviders()
  const def = ttsProviders.value.find(t => t.id === 1) || ttsProviders.value[0]
  if (def) {
    selectedTTS.value = def.id
    await loadVoices()
  }
}

const loadVoices = async () => {
  if (!selectedTTS.value) return
  const list = await fetchVoicesByTTS(selectedTTS.value)
  voices.value = list || []
  await clearTableSelection()
}

function openDialog(row) {
  if (row) {
    form.value = {
      id: row.id,
      name: row.name,
      reference_path: row.reference_path || '',
      tts_provider_id: row.tts_provider_id || selectedTTS.value || 1,
      tags: row.description ? row.description.split(',') : []
    }
  } else {
    form.value = {
      id: null,
      name: '',
      reference_path: '',
      tts_provider_id: selectedTTS.value || 1,
      tags: []
    }
  }
  dialogVisible.value = true
}

async function pickLocalAudioForBase() {
  const p = await native?.pickAudio?.()
  if (!p) return
  form.value.reference_path = p
}

function clearReferencePath() {
  form.value.reference_path = ''
}

// ====== 音频编辑器相关 ======
const waveEditorKey = ref(null)

function handleWaveReady(ws) {
  console.log('WaveCellPro ready', ws)
}

// 处理音频编辑确认
async function handleWaveConfirm(payload) {
  if (!editingVoice.value?.reference_path) return
  
  try {
    const res = await processVoiceAudio(editingVoice.value.reference_path, {
      speed: payload.speed,
      volume: payload.volume,
      start_ms: payload.start_ms,
      end_ms: payload.end_ms,
      silence_sec: payload.silence_sec,
      current_ms: payload.current_ms
    })
    
    if (res.code === 200) {
      ElMessage.success('音频处理完成')
      // 刷新编辑器
      waveEditorKey.value = Date.now()
    } else {
      ElMessage.error(res.message || '音频处理失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('音频处理失败')
  }
}

function toFileUrl(p) {
  try { return native.pathToFileUrl(p) } catch { return '' }
}

function submitForm() {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      const payload = {
        name: form.value.name,
        description: form.value.tags.length ? form.value.tags.join(',') : null,
        tts_provider_id: form.value.tts_provider_id,
        reference_path: form.value.reference_path || null
      }

      if (form.value.id) {
        // 添加id
        payload.id = form.value.id
        await updateVoice(form.value.id, payload)
        ElMessage.success('修改成功')
      } else {
        
        await createVoice(payload)
        ElMessage.success('创建成功')
      }

      dialogVisible.value = false
      await loadVoices()
    } catch (e) {
      console.error(e)
      ElMessage.error('操作失败')
    }
  })
}

async function handleDelete(id) {
  try {
    audioPlayer.pause()
    await deleteVoice(id)
    ElMessage.success('删除成功')
    await loadVoices()
  } catch {
    ElMessage.error('删除失败')
  }
}

async function handleBatchDelete() {
  const ids = selectedIds.value
  if (!ids.length) {
    ElMessage.warning('请先选择要删除的音色')
    return
  }

  audioPlayer.pause()

  const results = await Promise.allSettled(
    ids.map(id =>
      deleteVoice(id).then(res => {
        if (res?.code !== 200) throw new Error(res?.message || '删除失败')
        return res
      })
    )
  )

  const failed = results.filter(r => r.status === 'rejected')
  const successCount = ids.length - failed.length

  if (failed.length === 0) {
    ElMessage.success(`删除成功：${successCount} 个`)
  } else {
    ElMessage.warning(`删除完成：成功 ${successCount} 个，失败 ${failed.length} 个`)
  }

  await loadVoices()
}

onMounted(async () => {
  await loadTTS()
})

const tagSelectRef = ref(null)

function handleTagChange() {
  // 等 DOM 更新完再收起下拉框
  setTimeout(() => {
    tagSelectRef.value?.blur()
  }, 0)
}

function handleFilterTagChange() {
  setTimeout(() => {
    filterSelectRef.value?.blur()
  }, 0)
}

function resetFilters() {
  searchName.value = ''
  filterTags.value = []
}

async function handleExportSelected() {
  if (!selectedTTS.value) {
    ElMessage.warning('请先选择 TTS 引擎')
    return
  }
  const ids = selectedIds.value
  if (ids.length === 0) {
    ElMessage.warning('请先选择要导出的音色')
    return
  }

  try {
    const savePath = await native?.saveFile?.({
      title: '导出选中音色',
      defaultPath: 'voices_selected_export.zip',
      filters: [{ name: 'ZIP 文件', extensions: ['zip'] }]
    })

    if (!savePath) return

    const res = await exportVoices(selectedTTS.value, savePath, ids)
    if (res.code === 200) {
      ElMessage.success('导出成功：' + savePath)
    } else {
      ElMessage.error(res.message || '导出失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('导出失败')
  }
}

// ====== 导入音色库弹窗 ======
const importDialogVisible = ref(false)
const importForm = ref({
  zipPath: '',
  targetDir: ''
})

// 获取默认音色保存目录
function getDefaultVoiceDir() {
  // 默认为用户目录下的 SonicVale/voices
  const userHome = native?.getUserHome?.() || ''
  return userHome ? `${userHome}/SonicVale/voices` : ''
}

// 选择导入的zip文件
async function pickImportZip() {
  const zipPath = await native?.pickFile?.({
    title: '选择音色库文件',
    filters: [{ name: 'ZIP 文件', extensions: ['zip'] }]
  })
  if (zipPath) {
    importForm.value.zipPath = zipPath
  }
}

// 选择导入目标目录
async function pickImportDir() {
  const dir = await native?.pickDirectory?.({
    title: '选择音色保存目录'
  })
  if (dir) {
    importForm.value.targetDir = dir
  }
}

// 打开导入弹窗
async function handleImport() {
  if (!selectedTTS.value) {
    ElMessage.warning('请先选择 TTS 引擎')
    return
  }
  
  // 设置默认值
  importForm.value = {
    zipPath: '',
    targetDir: getDefaultVoiceDir()
  }
  importDialogVisible.value = true
}

// 确认导入
async function confirmImport() {
  if (!importForm.value.zipPath) {
    ElMessage.warning('请选择音色库文件')
    return
  }
  if (!importForm.value.targetDir) {
    ElMessage.warning('请设置音色保存目录')
    return
  }

  try {
    const res = await importVoices(
      selectedTTS.value, 
      importForm.value.zipPath, 
      importForm.value.targetDir
    )
    if (res.code === 200) {
      const data = res.data
      let msg = `导入完成：成功 ${data.success_count} 个`
      if (data.skipped_count > 0) {
        msg += `，跳过 ${data.skipped_count} 个（名称已存在）`
      }
      ElMessage.success(msg)
      importDialogVisible.value = false
      await loadVoices() // 刷新列表
    } else {
      ElMessage.error(res.message || '导入失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('导入失败')
  }
}

// ====== 复制音色弹窗 ======
const copyDialogVisible = ref(false)
const copyFormRef = ref(null)
const copyForm = ref({
  sourceId: null,
  sourceName: '',
  newName: '',
  targetDir: ''
})

const copyRules = {
  newName: [{ required: true, message: '请输入新音色名称', trigger: 'blur' }]
}

// 打开复制弹窗
function openCopyDialog(row) {
  copyForm.value = {
    sourceId: row.id,
    sourceName: row.name,
    newName: row.name + '_复制',
    targetDir: ''
  }
  copyDialogVisible.value = true
}

// 选择复制目标目录
async function pickCopyTargetDir() {
  const dir = await native?.pickDirectory?.({
    title: '选择新音色保存目录'
  })
  if (dir) {
    copyForm.value.targetDir = dir
  }
}

// 确认复制
async function confirmCopy() {
  if (!copyForm.value.newName) {
    ElMessage.warning('请输入新音色名称')
    return
  }

  try {
    const res = await copyVoice(
      copyForm.value.sourceId,
      copyForm.value.newName,
      copyForm.value.targetDir || null
    )
    if (res.code === 200) {
      ElMessage.success('复制成功')
      copyDialogVisible.value = false
      await loadVoices() // 刷新列表
    } else {
      ElMessage.error(res.message || '复制失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('复制失败')
  }
}

</script>

<style scoped>
.tag-hint {
  font-size: 12px;
  color: #409EFF; /* Element Plus 主色蓝 */
  margin-bottom: 6px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.page-header h2 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
}
.actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.filter-tags {
  width: 260px;
}
.filter-search {
  width: 220px;
}
.filter-result {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.tts-select {
  width: 240px;
}
.voice-table {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}
.tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.path-ellipsis {
  display: inline-block;
  max-width: 380px;
  vertical-align: middle;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-regular);
}
.pick-line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.preview {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.path-text {
  font-size: 12px;
  color: var(--el-text-color-regular);
  word-break: break-all;
}
.mb8 {
  margin-bottom: 8px;
}
.form-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
.wave-editor-wrap {
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
}
.audio-editor-info {
  margin-bottom: 16px;
  padding: 10px 12px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
}
.audio-editor-label {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.audio-editor-value {
  color: var(--el-text-color-primary);
  font-weight: 600;
  font-size: 14px;
}
</style>
