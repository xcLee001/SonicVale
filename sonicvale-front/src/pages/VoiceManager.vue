<template>
  <div>
    <div class="page-header">
      <h2>音色管理</h2>
      <div class="actions">
        <el-select v-model="selectedTTS" placeholder="选择 TTS 引擎" class="tts-select" @change="loadVoices">
          <el-option v-for="t in ttsProviders" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button type="primary" :disabled="!selectedTTS" @click="openDialog()">新增音色</el-button>
      </div>
    </div>

    <el-table
      :data="voices"
      border
      stripe
      highlight-current-row
      class="voice-table"
      :header-cell-style="headerCellStyle"
      :cell-style="cellStyle"
    >
      <el-table-column label="#" width="64" align="center">
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

      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column prop="updated_at" label="更新时间" width="180" />

      <el-table-column label="操作" width="180" fixed="right" align="center">
  <template #default="{ row }">
    <div class="flex justify-center gap-2">
      <el-button 
        type="primary" 
        size="small" 
        plain 
        @click="openDialog(row)">
        编辑
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
            <el-button v-if="form.reference_path" type="danger" link @click="form.reference_path = ''">清除</el-button>
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
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Headset } from '@element-plus/icons-vue'
import { createVoice, fetchVoicesByTTS, updateVoice, deleteVoice } from '../api/voice'
import { fetchTTSProviders } from '../api/provider'


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
watch(dialogVisible, v => { if (!v) audioPlayer.pause() })

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
  background: '#f7f8fa',
  color: '#303133',
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
    await deleteVoice(id)
    ElMessage.success('删除成功')
    await loadVoices()
  } catch {
    ElMessage.error('删除失败')
  }
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
  color: #606266;
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
  color: #666;
  word-break: break-all;
}
.mb8 {
  margin-bottom: 8px;
}
</style>
