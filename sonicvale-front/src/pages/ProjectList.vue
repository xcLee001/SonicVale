<template>
    <div>
        <!-- 标题 + 创建按钮 -->
        <div class="header-bar">
            <h2>项目管理</h2>
            <el-button type="primary" @click="dialogVisible = true">
                <el-icon>
                    <Plus />
                </el-icon>
                <span style="margin-left:4px;">新建项目</span>
            </el-button>
        </div>

        <!-- 项目卡片网格 -->
        <el-row :gutter="20">
            <el-col v-for="item in projects" :key="item.id" :xs="24" :sm="12" :md="8" :lg="6" :xl="6"
                style="margin-bottom:20px;">
                <el-card shadow="hover" class="project-card" :body-style="{ padding: '0px' }">
                    <!-- 卡片头部 -->
                    <div class="card-header">
                        <h3 class="project-title" :title="item.name">{{ item.name }}</h3>
                        <el-popconfirm title="确认删除这个项目吗？" confirm-button-text="删除" cancel-button-text="取消"
                            @confirm="handleDelete(item.id)">
                            <template #reference>
                                <el-button link type="danger" size="small">
                                    <el-icon>
                                        <Delete />
                                    </el-icon>
                                </el-button>
                            </template>
                        </el-popconfirm>
                    </div>

                    <!-- 项目信息 -->
                    <div class="project-card-body">
                        <p class="project-desc" :title="item.description">{{ item.description || '暂无描述' }}</p>

                        <div class="project-meta-grid">
                            <div v-if="item.llmProviderId" class="meta-item">
                                <el-icon><Cpu /></el-icon>
                                <span class="meta-label">LLM:</span>
                                <span class="meta-value">{{ getLLMProviderName(item.llmProviderId) }}</span>
                            </div>
                            <div v-if="item.ttsProviderId" class="meta-item">
                                <el-icon><Mic /></el-icon>
                                <span class="meta-label">TTS:</span>
                                <span class="meta-value">{{ getTTSProviderName(item.ttsProviderId) }}</span>
                            </div>
                            <div v-if="item.promptId" class="meta-item">
                                <el-icon><Document /></el-icon>
                                <span class="meta-label">提示词:</span>
                                <span class="meta-value">{{ getPromptName(item.promptId) }}</span>
                            </div>
                            <div class="meta-item">
                                <el-icon>
                                    <CircleCheck v-if="item.is_precise_fill == 1" class="precise-on" />
                                    <CircleClose v-else class="precise-off" />
                                </el-icon>
                                <span class="meta-label">精确填充:</span>
                                <el-tag size="small" :type="item.is_precise_fill == 1 ? 'success' : 'info'" effect="plain">
                                    {{ item.is_precise_fill == 1 ? '开启' : '关闭' }}
                                </el-tag>
                            </div>
                        </div>

                        <div class="project-footer">
                            <div class="time-info">
                                <el-icon><Clock /></el-icon>
                                <span>{{ new Date(item.createdAt).toLocaleDateString() }}</span>
                            </div>
                            <el-button type="primary" size="small" round
                                @click="$router.push(`/projects/${item.id}/dubbing`)">
                                🎙 继续配音
                            </el-button>
                        </div>
                    </div>
                </el-card>
            </el-col>
        </el-row>

        <!-- 创建项目弹窗 -->
        <el-dialog title="创建新项目" v-model="dialogVisible" width="500px">
            <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
                <!-- 项目名称 -->
                <el-form-item label="项目名称" prop="name">
                    <el-input v-model="form.name" placeholder="请输入项目名称"></el-input>
                </el-form-item>

                <!-- 项目描述 -->
                <el-form-item label="项目描述" prop="description">
                    <el-input v-model="form.description" type="textarea" placeholder="请输入项目描述" :rows="3"></el-input>
                </el-form-item>

                <!-- LLM 提供商 -->
                <el-form-item label="LLM 提供商">
                    <el-select v-model="form.llm_provider_id" placeholder="请选择 LLM 提供商" clearable style="width: 100%;">
                        <el-option v-for="provider in llmProviders" :key="provider.id" :label="provider.name"
                            :value="provider.id" />
                    </el-select>
                </el-form-item>

                <!-- LLM 模型 -->
                <el-form-item label="LLM 模型">
                    <el-select v-model="form.llm_model" placeholder="请选择 LLM 模型" clearable style="width: 100%;">
                        <el-option v-for="model in availableModels" :key="model" :label="model" :value="model" />
                    </el-select>
                </el-form-item>

                <!-- TTS 提供商 -->
                <el-form-item label="TTS 引擎">
                    <el-select v-model="form.tts_provider_id" placeholder="请选择 TTS 引擎" clearable style="width: 100%;">
                        <el-option v-for="tts in ttsProviders" :key="tts.id" :label="tts.name" :value="tts.id" />
                    </el-select>
                </el-form-item>
                <el-form-item v-if="selectedTTSEngineType === 'index_tts_2_5'" label="合成语言">
                    <el-select v-model="form.tts_language" style="width: 100%;">
                        <el-option label="中文" value="ZH" />
                        <el-option label="英语" value="EN" />
                        <el-option label="日语" value="JA" />
                        <el-option label="阿拉伯语" value="AR" />
                        <el-option label="西班牙语" value="ES" />
                    </el-select>
                </el-form-item>
                <!-- 提示词模板 -->
                <el-form-item label="提示词模板" prop="prompt_id">
                    <el-select v-model="form.prompt_id" placeholder="请选择提示词模板" clearable style="width: 100%;">
                        <el-option v-for="p in prompts" :key="p.id" :label="p.name" :value="p.id" />
                    </el-select>
                </el-form-item>
                <!-- ✅ 是否精确填充（0/1） -->
                <el-form-item label="精确填充">
                    <el-switch v-model="form.is_precise_fill" :active-value="1" :inactive-value="0" active-text="开启"
                        inactive-text="关闭" />
                </el-form-item>
                <!-- 项目根路径（可选） -->
                <!-- 项目根路径（选择文件夹 + 只读可复制） -->
                <el-form-item label="项目根路径" prop="project_root_path">
                    <el-input v-model="form.project_root_path" readonly
                        placeholder="例如：D:\\Works\\MyProject 或 /Users/me/Projects/demo">
                        <template #append>
                            <el-button @click="pickRootDir">选择</el-button>
                        </template>
                    </el-input>
                </el-form-item>




            </el-form>

            <template #footer>
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleSubmit">确定</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElLoading } from 'element-plus'
// import { Plus, Delete } from '@element-plus/icons-vue'
import { fetchProjects, createProject, deleteProject } from '../api/project'
import { fetchLLMProviders, fetchTTSProviders } from '../api/provider'
import { fetchPromptList } from '../api/prompt'
import { Plus, Delete, Cpu, Mic, Document, Clock, CircleCheck, CircleClose, Folder } from "@element-plus/icons-vue"
const prompts = ref([])

const projects = ref([])
const dialogVisible = ref(false)

// 表单数据
const form = ref({
    name: '',
    description: '',
    llm_provider_id: null,
    llm_model: null,
    tts_provider_id: null,
    tts_language: 'ZH',
    prompt_id: null,
    is_precise_fill: 0,      // ✅ 新增字段
    project_root_path: null,
})

// 校验规则
const rules = {
    name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
    description: [{ required: true, message: '请输入项目描述', trigger: 'blur' }],
    prompt_id: [{ required: true, message: '请选择提示词模版', trigger: 'change' }],
    project_root_path: [{ required: true, message: '请输入项目根路径', trigger: 'blur' }],
}

const formRef = ref(null)

// 下拉框数据
const llmProviders = ref([])
const availableModels = ref([])
const ttsProviders = ref([])
const selectedTTSEngineType = computed(() => {
    return ttsProviders.value.find(item => item.id === form.value.tts_provider_id)?.engine_type || ''
})

// 加载项目和 Provider 数据
onMounted(async () => {
    projects.value = await fetchProjects()
    llmProviders.value = await fetchLLMProviders()
    ttsProviders.value = await fetchTTSProviders()
    prompts.value = await fetchPromptList()   // ✅ 加载提示词
})


/** ===================== 名称映射工具 ===================== */
const getLLMProviderName = (id) => {
    const p = llmProviders.value.find(x => x.id === id)
    return p ? p.name : id
}
const getTTSProviderName = (id) => {
    const p = ttsProviders.value.find(x => x.id === id)
    console.log("getTTSProviderName", id, p)
    return p ? p.name : id
}
const getPromptName = (id) => {
    const p = prompts.value.find(x => x.id === id)
    return p ? p.name : id
}

// 监听 LLM provider 切换，更新模型列表
watch(
    () => form.value.llm_provider_id,
    (newVal) => {
        const provider = llmProviders.value.find(p => p.id === newVal)
        availableModels.value = provider ? provider.model_list.split(',') : []
        form.value.llm_model = null // 重置模型选择
    }
)

// 删除项目
const handleDelete = async (id) => {
    const loading = ElLoading.service({
        lock: true,
        text: '章节内容较多，删除较久，请稍等...',
        background: 'rgba(0, 0, 0, 0.3)',
    })

    try {
        await deleteProject(id)
        projects.value = projects.value.filter(p => p.id !== id)
        ElMessage.success('删除成功')
    } catch (e) {
        ElMessage.error('删除失败')
    } finally {
        loading.close()
    }
}


// 提交表单
const handleSubmit = () => {
    formRef.value.validate(async (valid) => {
        if (valid) {
            try {
                const res = await createProject(form.value)
                if (res?.code === 200) {
                    ElMessage.success('项目创建成功')
                    dialogVisible.value = false

                    // ✅ 重置表单
                    Object.assign(form.value, {
                        name: '',
                        description: '',
                        llm_provider_id: null,
                        llm_model: null,
                        tts_provider_id: null,
                        tts_language: 'ZH',
                        prompt_id: null,
                        is_precise_fill: 0,
                        project_root_path: null,
                    })

                    projects.value = await fetchProjects()
                } else {
                    // ✅ 正常请求但业务失败
                    ElMessage.error(`创建失败：${res?.message || '未知错误'}`)
                }
            } catch (e) {
                ElMessage.error(`创建失败：${e?.message || '网络异常'}`)
            }
        }
    })
}


const native = window.native
const pickRootDir = async () => {
    try {
        const dir = await native?.selectDir()
        if (dir) {
            form.value.project_root_path = dir
            // 如果设为必填，选完后立即触发该字段校验（可选）
            // formRef.value?.validateField?.('project_root_path')
        }
    } catch (e) {
        ElMessage.error(`选择失败：${e?.message || '未知错误'}`)
    }
}
</script>

<style scoped>
.header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.project-card {
    border-radius: 12px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    height: 100%;
    border: 1px solid var(--el-border-color-lighter);
}

.project-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
    border-color: #409eff;
}

/* 卡片头部 */
.card-header {
    padding: 14px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--el-border-color-lighter);
    background-color: var(--el-fill-color-light);
}

.project-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 180px;
}

.project-card-body {
    padding: 16px;
    display: flex;
    flex-direction: column;
    height: calc(100% - 49px);
}

.project-desc {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin: 0 0 16px 0;
    line-height: 1.5;
    height: 40px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}

.project-meta-grid {
    flex: 1;
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
    margin-bottom: 16px;
}

.meta-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--el-text-color-regular);
}

.meta-item .el-icon {
    font-size: 14px;
    color: var(--el-text-color-secondary);
}

.meta-label {
    color: var(--el-text-color-secondary);
    min-width: 60px;
}

.meta-value {
    color: var(--el-text-color-primary);
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.project-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 12px;
    border-top: 1px solid var(--el-border-color-lighter);
}

.time-info {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
}

.precise-on {
    color: #67C23A;
}

.precise-off {
    color: #F56C6C;
}
</style>
