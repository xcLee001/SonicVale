<template>
  <div>
    <h2 style="margin-bottom:16px;">配置中心</h2>

    <el-tabs v-model="activeTab">
      <!-- LLM 管理 -->
      <el-tab-pane label="LLM 管理" name="llm">
        <div class="toolbar">
          <el-button type="primary" @click="openLLMDialog()">新增 LLM 提供商</el-button>
        </div>

        <el-table :data="llmList" stripe border highlight-current-row class="styled-table">
          <el-table-column prop="name" label="名称" min-width="160" />
          <el-table-column prop="api_base_url" label="Base URL" min-width="240" />
          <el-table-column prop="model_list" label="模型列表" min-width="240" />
          <el-table-column label="API Key" min-width="180">
            <template #default="{ row }">
              <span class="api-key">{{ maskKey(row.api_key) }}</span>
            </template>
          </el-table-column>



          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag effect="light" :type="row.status === 1 ? 'success' : 'info'">
                <span class="status-dot" :class="row.status === 1 ? 'dot-green' : 'dot-gray'"></span>
                {{ row.status === 1 ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>

          <!-- <el-table-column prop="updated_at" label="更新于" min-width="180" /> -->

          <el-table-column label="操作" width="180" fixed="right" align="center">
            <template #default="{ row }">
              <div class="flex justify-center gap-2">
                <el-button type="primary" size="small" plain @click="openLLMDialog(row)">
                  编辑
                </el-button>

                <el-popconfirm title="确认删除该 LLM 提供商？" confirm-button-text="确定" cancel-button-text="取消"
                  @confirm="removeLLM(row.id)">
                  <template #reference>
                    <el-button type="danger" size="small" plain>
                      删除
                    </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </template>
          </el-table-column>

        </el-table>
      </el-tab-pane>

      <!-- TTS 管理（列表，仅编辑） -->
      <el-tab-pane label="TTS 管理" name="tts">
        <div class="toolbar">
          <el-button type="primary" disabled>仅支持编辑，不可新增/删除</el-button>
        </div>

        <el-table :data="ttsList" stripe border highlight-current-row class="styled-table">
          <el-table-column prop="name" label="名称" min-width="160" />
          <el-table-column prop="api_base_url" label="Base URL" min-width="240" />

          <el-table-column label="API Key" min-width="180">
            <template #default="{ row }">
              <span class="api-key">{{ maskKey(row.api_key) }}</span>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag effect="light" :type="row.status === 1 ? 'success' : 'info'">
                <span class="status-dot" :class="row.status === 1 ? 'dot-green' : 'dot-gray'"></span>
                {{ row.status === 1 ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>

          <!-- <el-table-column prop="updated_at" label="更新于" min-width="180" /> -->

          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" plain @click="openTTSDialog(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- LLM 弹窗 -->
    <el-dialog :title="llmForm.id ? '编辑 LLM 提供商' : '新增 LLM 提供商'" v-model="llmDialogVisible" width="560px">
      <el-form :model="llmForm" :rules="llmRules" ref="llmFormRef" label-width="110px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="llmForm.name" placeholder="如：DeepSeek" />
        </el-form-item>
        <el-form-item label="Base URL" prop="api_base_url">
          <el-input v-model="llmForm.api_base_url" placeholder="https://api.xxx.com" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="llmForm.api_key" placeholder="可留空" show-password />
        </el-form-item>
        <el-form-item label="模型列表">
          <el-input v-model="llmForm.model_list" placeholder="用英文逗号分隔" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="llmForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="自定义参数" prop="custom_params">
          <el-input type="textarea" v-model="llmForm.custom_params" :rows="6" placeholder='请输入 JSON 格式参数' />
        </el-form-item>

      </el-form>

      <template #footer>
        <!-- 新增测试按钮 -->
        <el-button type="warning" @click="testLLM">测试</el-button>
        <el-button @click="llmDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitLLM">确定</el-button>
      </template>
    </el-dialog>

    <!-- TTS 弹窗（编辑） -->
    <el-dialog title="编辑 TTS 引擎" v-model="ttsDialogVisible" width="560px">
      <el-form :model="ttsForm" :rules="ttsRules" ref="ttsFormRef" label-width="110px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="ttsForm.name" placeholder="如：Index_TTS" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="ttsForm.api_base_url" placeholder="可留空" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="ttsForm.api_key" placeholder="可留空" show-password />
        </el-form-item>

        <el-form-item label="状态">
          <el-switch v-model="ttsForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>

      </el-form>

      <template #footer>
        <!-- 新增测试按钮 -->
        <el-button type="warning" @click="testTTS">测试</el-button>
        <el-button @click="ttsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTTS">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>



<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchLLMProviders, createLLMProvider, updateLLMProvider, deleteLLMProvider,
  fetchTTSProviders, updateTTSProvider, testLLMProvider, testTTSProvider
} from '../api/provider'

const activeTab = ref('llm')

// ---------- LLM ----------
const llmList = ref([])

const loadLLM = async () => { llmList.value = await fetchLLMProviders() }

const llmDialogVisible = ref(false)
const llmFormRef = ref()
const DEFAULT_CUSTOM_PARAMS = JSON.stringify(
  {
    response_format: { type: 'json_object' },
    temperature: 0.7,
    top_p: 0.9
  },
  null,
  2  // 漂亮一点，换行缩进
)

const llmForm = ref({
  id: null,
  name: '',
  api_base_url: '',
  api_key: '',
  model_list: '',
  status: 1,
  custom_params: DEFAULT_CUSTOM_PARAMS
})
const llmRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  api_base_url: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }],
  custom_params: [
    {
      required: true,
      message: '自定义参数不能为空，至少为 {}',
      trigger: 'blur'
    },
    {
      validator: (rule, value, callback) => {
        const v = (value || '').trim()
        if (!v) {
          return callback(new Error('自定义参数不能为空，至少为 {}'))
        }
        try {
          JSON.parse(v)
          callback()
        } catch (e) {
          callback(new Error('自定义参数必须是合法 JSON 格式'))
        }
      },
      trigger: 'blur'
    }
  ]
}
function openLLMDialog(row) {
  if (row) llmForm.value = { ...row }
  else llmForm.value = { id: null, name: '', api_base_url: '', api_key: '', model_list: '', status: 1, custom_params: DEFAULT_CUSTOM_PARAMS }
  llmDialogVisible.value = true
}
function submitLLM() {
  llmFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      if (llmForm.value.id) {
        await updateLLMProvider(llmForm.value.id, llmForm.value)
        ElMessage.success('已更新')
      } else {
        await createLLMProvider(llmForm.value)
        ElMessage.success('已创建')
      }
      llmDialogVisible.value = false
      await loadLLM()
    } catch {
      ElMessage.error('操作失败')
    }
  })
}
async function removeLLM(id) {
  try {
    await deleteLLMProvider(id)
    ElMessage.success('已删除')
    await loadLLM()
  } catch {
    ElMessage.error('删除失败')
  }
}


import { ElLoading } from 'element-plus'

async function testLLM() {
  // 打开等待框
  const loading = ElLoading.service({
    lock: true,
    text: '正在测试，请稍候...',
    background: 'rgba(0, 0, 0, 0.4)'
  })

  try {
    const res = await testLLMProvider(llmForm.value)
    if (res.code === 200) {
      ElMessage.success(res.message || '测试成功')
    } else {
      ElMessage.error(res.message || '测试失败')
    }
  } catch (e) {
    ElMessage.error('测试异常')
  } finally {
    // 关闭等待框
    loading.close()
  }
}



// ---------- TTS ----------
const ttsList = ref([])
const ttsDialogVisible = ref(false)
const ttsFormRef = ref()
const ttsForm = ref({
  id: 1,
  name: '',
  api_base_url: '',
  api_key: '',
  status: 1,
})
const ttsRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

const loadTTS = async () => {
  const list = await fetchTTSProviders()
  ttsList.value = Array.isArray(list) ? list : []
}

function openTTSDialog(row) {
  ttsForm.value = { ...row }
  ttsDialogVisible.value = true
}

function submitTTS() {
  ttsFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await updateTTSProvider(ttsForm.value.id, ttsForm.value)
      ElMessage.success('已更新')
      ttsDialogVisible.value = false
      await loadTTS()
    } catch {
      ElMessage.error('操作失败')
    }
  })
}



async function testTTS() {
  const loading = ElLoading.service({
    lock: true,
    text: '正在测试 TTS，请稍候...',
    background: 'rgba(0, 0, 0, 0.4)'
  })

  try {
    console.log('ttsForm.value', ttsForm.value)
    const res = await testTTSProvider(ttsForm.value)
    if (res.code === 200) {
      ElMessage.success(res.message || 'TTS 测试成功')
    } else {
      ElMessage.error(res.message || 'TTS 测试失败')
    }
  } catch (e) {
    ElMessage.error('TTS 测试异常')
  } finally {
    loading.close()
  }
}



// ---------- 工具 ----------
const maskKey = (val) => (val ? '•'.repeat(Math.min(val.length, 8)) : '（未设置）')

onMounted(async () => {
  await Promise.all([loadLLM(), loadTTS()])
})
</script>

<style scoped>
.toolbar {
  margin-bottom: 12px;
}

.masked {
  margin-right: 8px;
}

.styled-table {
  border-radius: 10px;
  overflow: hidden;
  font-size: 14px;
}

.styled-table ::v-deep(.el-table__header th) {
  background-color: var(--el-fill-color-light);
  font-weight: 600;
  text-align: center;
}

.styled-table ::v-deep(.el-table__body td) {
  text-align: center;
}

.api-key {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}

.dot-green {
  background: #67c23a;
}

.dot-gray {
  background: #909399;
}
</style>
