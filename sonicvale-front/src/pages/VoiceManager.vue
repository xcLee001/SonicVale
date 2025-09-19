<template>
  <div>
    <div class="page-header">
      <h2>音色管理</h2>
      <div class="actions">
        <el-select v-model="selectedTTS" placeholder="选择 TTS 引擎" class="tts-select" @change="loadVoices">
          <el-option v-for="t in ttsProviders" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
        <el-button type="primary" :disabled="!selectedTTS" @click="openDialog()">新增音色</el-button>
        <!-- <el-button type="success" :disabled="!selectedTTS" @click="importMultiEmotionVoiceFromFolder">
  批量导入情绪音色
</el-button> -->
      </div>
    </div>

    <el-table :data="voices" border stripe highlight-current-row class="voice-table"
      :header-cell-style="headerCellStyle" :cell-style="cellStyle">
      <el-table-column label="#" width="64" align="center">
        <template #default="{ $index }">{{ $index + 1 }}</template>
      </el-table-column>

      <el-table-column prop="name" label="名称" min-width="180" />

      <el-table-column label="类型" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_multi_emotion ? 'success' : 'info'" effect="plain">
            {{ row.is_multi_emotion ? '多情绪' : '单一' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="播放" width="160" align="center">
        <template #default="{ row }">
          <!-- 统一使用 togglePlay，按钮文案根据状态切换 -->
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

      <el-table-column prop="description" label="描述" min-width="220">
        <template #default="{ row }">
          <span class="desc" :title="row.description">{{ row.description || '—' }}</span>
        </template>
      </el-table-column>

      <el-table-column label="参考音频/路径" min-width="200" align="center">
        <template #default="{ row }">
          <template v-if="!row.is_multi_emotion">
            <el-tooltip :content="row.reference_path ? row.reference_path : '未设置参考音频'" placement="top">
              <span class="path-ellipsis">{{ row.reference_path || '（未设置）' }}</span>
            </el-tooltip>
          </template>
          <template v-else>
            <span class="muted">随情绪配置</span>
          </template>
        </template>
      </el-table-column>

      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column prop="updated_at" label="更新时间" width="180" />

      <el-table-column label="操作" width="200" fixed="right" align="center">
        <template #default="{ row }">
          <el-button type="primary" link @click="openDialog(row)">编辑</el-button>
          <el-popconfirm title="确认删除该音色？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button type="danger" link>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 弹窗：新增/编辑 -->
    <el-dialog :title="form.id ? '编辑音色' : '新增音色'" v-model="dialogVisible" width="900px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入音色名称" />
        </el-form-item>

        <!-- <el-form-item label="音色类型" prop="is_multi_emotion">
          <el-radio-group v-model="form.is_multi_emotion">
            <el-radio :label="false">单一音色</el-radio>
            <el-radio :label="true">多情绪音色</el-radio>
          </el-radio-group>
        </el-form-item> -->

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>

        <!-- 单一音色：参考音频（本地路径） -->
        <template v-if="!form.is_multi_emotion">
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
        </template>

        <!-- 多情绪音色：情绪枚举 + 强度枚举 + 每行参考音频 -->
        <template v-else>
          <el-form-item label="情绪音色" required>
            <div class="ev-wrap">
              <el-table :data="form.emotion_voices" border class="ev-table" :height="400">
                <el-table-column label="#" width="56" align="center">
                  <template #default="{ $index }">{{ $index + 1 }}</template>
                </el-table-column>
                <el-table-column label="情绪" width="160">
                  <template #default="{ row }">
                    <el-select v-model="row.emotion_id" placeholder="选择情绪" filterable>
                      <el-option v-for="opt in emotionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                    </el-select>
                  </template>
                </el-table-column>

                <el-table-column label="强度" width="160">
                  <template #default="{ row }">
                    <el-select v-model="row.strength_id" placeholder="选择强度" filterable>
                      <el-option v-for="opt in strengthOptions" :key="opt.value" :label="opt.label"
                        :value="opt.value" />
                    </el-select>
                  </template>
                </el-table-column>

                <el-table-column label="参考音频" min-width="260">
                  <template #default="{ row, $index }">
                    <div class="pick-line">
                      <el-input v-model="row.reference_path" placeholder="请选择本地音频文件" readonly />
                      <el-button @click="pickLocalAudioForVariant($index)">选择</el-button>
                      <el-button v-if="row.reference_path" type="danger" link
                        @click="row.reference_path = ''">清除</el-button>
                      <el-button
                        v-if="row.reference_path"
                        size="small"
                        type="primary"
                        plain
                        @click="togglePlay(row.reference_path)"
                      >
                        {{ isPlaying && currentPath === row.reference_path ? '暂停' : '播放' }}
                      </el-button>
                    </div>
                    <div v-if="row.reference_path" class="path-text">{{ row.reference_path }}</div>
                  </template>
                </el-table-column>
                <!-- <el-table-column label="备注" min-width="160">
                  <template #default="{ row }">
                    <el-input v-model="row.description" placeholder="可选" />
                  </template>
                </el-table-column> -->
                <el-table-column label="操作" width="100" align="center">
                  <template #default="{ $index }">
                    <el-button type="danger" link @click="removeEmotionRow($index)">移除</el-button>
                  </template>
                </el-table-column>
              </el-table>

              <div class="mt8">
                <el-button type="primary" plain icon="Plus" @click="addEmotionRow">添加情绪音色</el-button>
                <span class="muted ml8">情绪/强度来自枚举（只读），同一组合不可重复。</span>
              </div>
            </div>
          </el-form-item>
        </template>
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
import { ElMessage,ElMessageBox } from 'element-plus'
import { Headset } from '@element-plus/icons-vue'
import { createVoice, fetchVoicesByTTS, updateVoice, deleteVoice } from '../api/voice'
import { fetchTTSProviders } from '../api/provider'
// 假设新增两个只读枚举查询接口（不可增删）
import { fetchAllEmotions, fetchAllStrengths } from '../api/enums'
import { fetchMultiEmotionVoicesByVoiceId, createMultiEmotionVoice, deleteMultiEmotionVoice,updateMultiEmotionVoice } from '../api/multiEmotionVoice'
import { de } from 'element-plus/es/locales.mjs'

// @ts-ignore - 由 preload 暴露
const native = window.native

const ttsProviders = ref([])
const selectedTTS = ref(null)
const voices = ref([])

// ====== 统一音频播放控制（优雅版）======
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

  // 同一文件：切换暂停/继续
  if (currentPath.value === absPath) {
    if (isPlaying.value) {
      audioPlayer.pause()
    } else {
      audioPlayer.play().catch(() => ElMessage.error('无法播放该音频文件'))
    }
    return
  }

  // 切到新文件：从头播放
  audioPlayer.pause()
  audioPlayer.src = url
  audioPlayer.currentTime = 0
  currentPath.value = absPath
  audioPlayer.play().catch(() => ElMessage.error('无法播放该音频文件'))
}

// 同步播放状态到 UI
audioPlayer.addEventListener('play', () => { isPlaying.value = true })
audioPlayer.addEventListener('pause', () => { isPlaying.value = false })
audioPlayer.addEventListener('ended', () => {
  isPlaying.value = false
  currentPath.value = null
})
// 关闭弹窗时自动暂停
const dialogVisible = ref(false)
watch(dialogVisible, v => { if (!v) audioPlayer.pause() })
// =====================================

const formRef = ref(null)
const form = ref({
  id: null,
  name: '',
  description: '',
  // 单一音色使用
  reference_path: '',
  tts_provider_id: null,
  // 多情绪音色
  is_multi_emotion: false,
  emotion_voices: [] // { emotion_id, strength_id, reference_path }
})

const rules = {
  name: [{ required: true, message: '请输入音色名称', trigger: 'blur' }],
  is_multi_emotion: [{ required: true, message: '请选择音色类型', trigger: 'change' }]
}

const emotionOptions = ref([]) // [{ value: 'neutral', label: '中性' }, ...]
const strengthOptions = ref([]) // [{ value: 'low', label: '低' }, ...]

// 将后端返回的列表映射为下拉选项：优先使用 code 作为 value，其次 name
function mapToOptions(list) {
  return list.map(e => ({ value: e.id, label: e.name }))
}

// 表格样式
const headerCellStyle = () => ({
  background: '#f7f8fa',
  color: '#303133',
  fontWeight: 600
})
const cellStyle = () => ({
  padding: '10px 12px'
})

// 默认选中 id=1 的 index_tts
const loadTTS = async () => {
  ttsProviders.value = await fetchTTSProviders()
  const def = ttsProviders.value.find(t => t.id === 1) || ttsProviders.value[0]
  if (def) {
    selectedTTS.value = def.id
    await loadVoices()
  }
}

const loadEnums = async () => {
  const [emos, strengths] = await Promise.all([
    fetchAllEmotions(),
    fetchAllStrengths()
  ])

  emotionOptions.value = mapToOptions(emos)
  strengthOptions.value = mapToOptions(strengths)
  console.log('emos', emotionOptions.value)
  console.log('strengths', strengthOptions.value)

}

const loadVoices = async () => {
  if (!selectedTTS.value) return
  const list = await fetchVoicesByTTS(selectedTTS.value)
  // 兼容后端返回结构：包含 is_multi_emotion 和 emotion_voices 数组
  voices.value = list || []
}

// 加在多情绪音色列表
async function loadVariantsForVoice(voiceId) {
  try {
    const res = await fetchMultiEmotionVoicesByVoiceId(voiceId)
    console.log('loadVariantsForVoice', res)
    form.value.emotion_voices = (res.data || []).map(ev => ({
      id: ev.id,
      emotion_id: ev.emotion_id,
      strength_id: ev.strength_id,
      reference_path: ev.reference_path || ''
    }))
    console.log('form emotion_voices', form.value.emotion_voices)
  } catch (e) {
    console.error('加载多情绪音色失败', e)
  }
}
function openDialog(row) {
  if (row) {
    form.value = {
      id: row.id,
      name: row.name,
      description: row.description || '',
      reference_path: row.reference_path || '',
      tts_provider_id: row.tts_provider_id || selectedTTS.value || 1,
      is_multi_emotion: !!row.is_multi_emotion,
      emotion_voices: (row.emotion_voices || []).map(ev => ({
        id: ev.id,
        emotion_id: ev.emotion_id,
        strength_id: ev.strength_id,
        reference_path: ev.reference_path || ''
      }))
    }
    // 关键：弹窗一开就请求多情绪条目并覆盖
    if (form.value.is_multi_emotion && form.value.id) {
      loadVariantsForVoice(form.value.id)
    }
  } else {
    form.value = {
      id: null,
      name: '',
      description: '',
      reference_path: '',
      tts_provider_id: selectedTTS.value || 1,
      is_multi_emotion: false,
      emotion_voices: []
    }
  }
  dialogVisible.value = true
}

async function pickLocalAudioForBase() {
  const p = await native?.pickAudio?.()
  if (!p) return
  form.value.reference_path = p
}

async function pickLocalAudioForVariant(index) {
  const p = await native?.pickAudio?.()
  if (!p) return
  form.value.emotion_voices[index].reference_path = p
}

function addEmotionRow() {
  form.value.emotion_voices.push({ emotion_id: '', strength_id: '', reference_path: '' })
  console.log('addEmotionRow', form.value.emotion_voices)
}

async function removeEmotionRow(i) {
  const rows = form.value.emotion_voices || []
  const row = rows[i]
  if (!row) return

  try {
    await ElMessageBox.confirm(
      '确认删除该情绪音色？此操作不可恢复。',
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )

    await deleteMultiEmotionVoice(row.id)
    ElMessage.success('删除成功')

    // 删完重新拉取，确保与服务端一致
    await loadVariantsForVoice(form.value.id)

  } catch (err) {
    // 用户取消
    if (err === 'cancel' || err === 'close') return
    console.error('删除多情绪音色失败', err)
    ElMessage.error('删除失败')
  }
}

function toFileUrl(p) {
  try { return native.pathToFileUrl(p) } catch { return '' }
}

function checkMultiEmotionValid() {
  if (!form.value.is_multi_emotion) return true
  const rows = form.value.emotion_voices || []
  if (!rows.length) {
    ElMessage.error('请至少添加一条情绪音色')
    return false
  }
  // 字段完整性
  for (const [i, r] of rows.entries()) {
    if (!r.emotion_id || !r.strength_id) {
      ElMessage.error(`第 ${i + 1} 行：请选择情绪与强度`)
      return false
    }
  }
  // 组合唯一性
  const keys = rows.map(r => `${r.emotion_id}__${r.strength_id}`)
  const dup = keys.find((k, i) => keys.indexOf(k) !== i)
  if (dup) {
    ElMessage.error('情绪 + 强度 组合不能重复')
    return false
  }
  return true
}

function submitForm() {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    // if (!checkMultiEmotionValid()) return
    try {
      const basePayload = {
        name: form.value.name,
        description: form.value.description || null,
        tts_provider_id: form.value.tts_provider_id,
        is_multi_emotion: !!form.value.is_multi_emotion
      }

      let payload
      const firstEmotion = form.value.emotion_voices?.[0] || null
      if (form.value.is_multi_emotion) {
        payload = {
          ...basePayload,
          reference_path: firstEmotion?.reference_path || null,
          emotion_voices: form.value.emotion_voices.map(ev => ({
            id: ev.id || null,
            emotion_id: ev.emotion_id,
            strength_id: ev.strength_id,
            reference_path: ev.reference_path || null
          }))
        }
      } else {
        payload = {
          ...basePayload,
          reference_path: form.value.reference_path || null,
          emotion_voices: []
        }
      }
      let voice_id = null
      if (form.value.id) {
        voice_id  = form.value.id
        await updateVoice(form.value.id, payload)
        ElMessage.success('修改成功')
      } else {
        const res = await createVoice(payload)
        voice_id = res.data.id
        ElMessage.success('创建成功')
      }
      console.log('voice_id', voice_id)
      // 对于emotion_voices中的每一个，若有id则更新，无id则创建
      if (form.value.is_multi_emotion && payload.emotion_voices.length) {
        for (const ev of payload.emotion_voices) {
          if (ev.id) {
            console.log('更新多音色', ev)
            await updateMultiEmotionVoice(ev.id, { ...ev, voice_id })
          } else {
            console.log('创建多音色', ev)
            await createMultiEmotionVoice({ ...ev, voice_id })
          }
        }
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

function displayEmotion(val) {
  const it = emotionOptions.value.find(x => x.value === val)
  return it ? it.label : val || '—'
}
function displayStrength(val) {
  const it = strengthOptions.value.find(x => x.value === val)
  return it ? it.label : val || '—'
}

onMounted(async () => {
  await Promise.all([loadTTS(), loadEnums()])
})

async function importMultiEmotionVoiceFromFolder() {
  const fileList = await native?.selectVoiceFolder?.()
  if (!fileList || !fileList.length) {
    ElMessage.warning('未选择文件夹或文件夹为空')
    return
  }

  // 构建 name → id 的映射
  const emotionMap = Object.fromEntries(emotionOptions.value.map(e => [e.label, e.value]))
  const strengthMap = Object.fromEntries(strengthOptions.value.map(s => [s.label, s.value]))

  const voiceName = fileList[0].voice_name

  // 查找或创建 voice
  let voiceId = null
  const exist = voices.value.find(v => v.name === voiceName)
  if (exist) {
    voiceId = exist.id
  } else {
    const res = await createVoice({
      name: voiceName,
      description: '批量导入',
      tts_provider_id: selectedTTS.value,
      is_multi_emotion: true,
      reference_path: null,
      emotion_voices: []
    })
    voiceId = res?.data?.id
    ElMessage.success(`已创建音色「${voiceName}」`)
    await loadVoices()
  }

  // 创建每个 emotion + strength 音色配置
  let created = 0
  for (const item of fileList) {
    const emotion_id = emotionMap[item.emotion_name]
    const strength_id = strengthMap[item.strength_name]

    if (!emotion_id || !strength_id) {
      console.warn('未匹配的枚举：', item)
      continue
    }

    const payload = {
      voice_id: voiceId,
      emotion_id,
      strength_id,
      reference_path: item.reference_path
    }

    try {
      await createMultiEmotionVoice(payload)
      created++
    } catch (err) {
      console.error('创建失败：', payload, err)
    }
  }

  ElMessage.success(`成功导入 ${created} 条情绪音色`)
  await loadVoices()
}
</script>

<style scoped>
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
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.desc {
  color: #606266;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.mt8 {
  margin-top: 8px;
}

.ml8 {
  margin-left: 8px;
}

.mr4 {
  margin-right: 4px;
}

.muted {
  color: #999;
}

.ev-wrap {
  width: 100%;
}

.ev-table :deep(.el-input__inner) {
  height: 32px;
}

.ev-pop {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ev-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.ev-text {
  font-size: 13px;
}

.voice-dialog :deep(.el-dialog__body) {
  max-height: 78vh;
  overflow: auto;
}
</style>
