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
                <el-card shadow="hover" class="project-card">
                    <!-- 删除按钮 -->
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
                    <!-- 项目信息 -->
                    <div style="padding:14px;">
                        <h3 class="project-title">{{ item.name }}</h3>
                        <p class="project-desc">{{ item.description }}</p>
                        <p class="project-meta">创建日期：{{ item.createdAt }}</p>
                        <p class="project-meta">更新日期：{{ item.updatedAt }}</p>

                        <p v-if="item.llmProviderId" class="project-meta">
                            LLM 提供商：{{ getLLMProviderName(item.llmProviderId) }}
                        </p>
                        <p v-if="item.llmModel" class="project-meta">
                            LLM 模型：{{ item.llmModel }}
                        </p>
                        <p v-if="item.ttsProviderId" class="project-meta">
                            TTS 引擎：{{ getTTSProviderName(item.ttsProviderId) }}
                        </p>

                        <div style="text-align:right; margin-top:12px;">
                            <el-button size="small" type="primary" @click="$router.push(`/projects/${item.id}/dubbing`)">继续配音</el-button>
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
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { fetchProjects, createProject, deleteProject } from '../api/project'
import { fetchLLMProviders, fetchTTSProviders } from '../api/provider'

const projects = ref([])
const dialogVisible = ref(false)

// 表单数据
const form = ref({
    name: '',
    description: '',
    llm_provider_id: null,
    llm_model: null,
    tts_provider_id: null
})

// 校验规则
const rules = {
    name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
    description: [{ required: true, message: '请输入项目描述', trigger: 'blur' }]
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
    try {
        await deleteProject(id)
        projects.value = projects.value.filter(p => p.id !== id)
        ElMessage.success('删除成功')
    } catch (e) {
        ElMessage.error('删除失败')
    }
}

// 提交表单
const handleSubmit = () => {
    formRef.value.validate(async (valid) => {
        if (valid) {
            try {
                await createProject(form.value)
                ElMessage.success('项目创建成功')
                dialogVisible.value = false
                // 重置表单
                Object.assign(form.value, { name: '', description: '', llm_provider_id: null, llm_model: null, tts_provider_id: null })
                projects.value = await fetchProjects()
            } catch (e) {
                ElMessage.error('创建失败')
            }
        }
    })
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
    overflow: hidden;
    position: relative;
}

.delete-btn {
    position: absolute;
    top: 10px;
    right: 10px;
}

.project-title {
    margin-bottom: 6px;
    font-size: 16px;
    font-weight: bold;
}

.project-desc {
    font-size: 13px;
    color: #999;
    margin: 0 0 8px;
}

.project-meta {
    font-size: 14px;
    color: #666;
    margin: 0 0 4px;
}
</style>
