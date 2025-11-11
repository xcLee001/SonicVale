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
        <el-row :gutter="40">
            <el-col v-for="item in projects" :key="item.id" :xs="24" :sm="12" :md="8" :lg="6" :xl="6"
                style="margin-bottom:20px;">
                <el-card shadow="hover" class="project-card">
                    <!-- 删除按钮（悬浮右上角） -->
                    <div class="delete-btn">
                        <el-popconfirm title="确认删除这个项目吗？" confirm-button-text="删除" cancel-button-text="取消"
                            @confirm="handleDelete(item.id)">
                            <template #reference>
                                <el-button size="small" circle type="danger" plain>
                                    <el-icon>
                                        <Delete />
                                    </el-icon>
                                </el-button>
                            </template>
                        </el-popconfirm>
                    </div>

                    <!-- 项目信息 -->
                    <div class="project-card-body">
                        <h3 class="project-title">{{ item.name }}</h3>
                        <p class="project-desc">{{ item.description || '暂无描述' }}</p>

                        <div class="project-meta-list">
                            <p v-if="item.llmProviderId" class="project-meta">
                                <el-icon>
                                    <Cpu />
                                </el-icon> LLM 提供商：{{ getLLMProviderName(item.llmProviderId) }}
                            </p>
                            <p v-if="item.llmModel" class="project-meta">
                                <el-icon>
                                    <Cpu />
                                </el-icon> LLM 模型：{{ item.llmModel }}
                            </p>
                            <p v-if="item.ttsProviderId" class="project-meta">
                                <el-icon>
                                    <Mic />
                                </el-icon> TTS 引擎：{{ getTTSProviderName(item.ttsProviderId) }}
                            </p>
                            <p v-if="item.promptId" class="project-meta">
                                <el-icon>
                                    <Document />
                                </el-icon> 提示词：{{ getPromptName(item.promptId) }}
                            </p>
                            <!-- ✅ 精确填充状态 + 图标 -->
                            <p class="project-meta" :class="item.is_precise_fill == 1 ? 'precise-on' : 'precise-off'">
                                <el-icon>
                                    <CircleCheck v-if="item.is_precise_fill == 1" />
                                    <CircleClose v-else />
                                </el-icon>
                                精确填充：{{ item.is_precise_fill == 1 ? '开启' : '关闭' }}
                            </p>

                            <!-- 更新时间 -->
                            <p class="project-meta">
                                <el-icon>
                                    <Clock />
                                </el-icon> 创建时间：{{ new Date(item.createdAt).toLocaleString() }}
                            </p>
                            <p class="project-meta">
                                <el-icon>
                                    <Folder />
                                </el-icon>
                                根路径：{{ item.project_root_path }}
                            </p>



                        </div>

                        <!-- 操作按钮 -->
                        <div class="project-actions">
                            <el-button size="small" type="primary" round
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
import { ref, onMounted, watch } from 'vue'
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
    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
}

.project-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
}

/* 删除按钮悬浮 */
.delete-btn {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 1;
}

.project-card-body {
    padding: 12px;
    display: flex;
    flex-direction: column;
    height: 100%;
}

.project-title {
    font-size: 18px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 6px 0;
}

.project-desc {
    font-size: 14px;
    color: #606266;
    line-height: 1.5;
    margin-bottom: 10px;
    min-height: 36px;
}

.project-meta-list {
    flex: 1;
    margin-top: 8px;
}

.project-meta {
    font-size: 13px;
    color: #909399;
    margin: 2px 0;
    display: flex;
    overflow: hidden;
    align-items: center;
    gap: 4px;
}

.project-actions {
    text-align: right;
    margin-top: 14px;
}

.precise-on {
    color: #67C23A;
    /* 绿色，表示开启 */
}

.precise-off {
    color: #F56C6C;
    /* 红色，表示关闭 */
}
</style>
