<template>
  <div class="prompt-manager">
    <!-- 顶部栏 -->
    <div class="header-bar">
      <h2 class="page-title">提示词管理</h2>
      <div class="toolbar">
        <el-input v-model="search" placeholder="搜索提示词名称" style="width: 200px; margin-right: 10px" clearable
          @clear="loadPrompts" @input="loadPrompts" />
        <el-button type="primary" @click="openDialog()">新增提示词</el-button>
      </div>
    </div>
    <!-- 公告栏 -->

    <!-- 公告按钮 -->
    <el-button type="danger" plain round right @click="noticeVisible = true">
      <el-icon style="margin-right: 6px;">
        <WarningFilled />
      </el-icon>
      提示词说明
    </el-button>


    <!-- 公告弹框 -->
    <el-dialog v-model="noticeVisible" title="📢 提示词必备格式说明" width="750px">
      <div class="notice-content">
        <p>⚠️ 创建提示词时，必须遵守以下规则，否则会创建失败：</p>

        <p>
          ✅ 必须包含 <strong>小说原文</strong>：
          <code>
&lt;novel_content&gt;<br />
{novel_content}<br />
&lt;/novel_content&gt;
      </code>
        </p>

        <p style="color: #e53935; font-weight: bold;">
  ⚠️ 注意：<strong>输出必须严格为 JSON 格式！</strong><br>
  <span style="color: #999; font-weight: normal;">
    （不再使用 <code>&lt;result&gt;</code> 标签格式）
  </span>
</p>



        <p>
          ✅ <strong>输出 JSON 数组</strong> 中的每个对象必须包含以下四个参数：
          <code>
{<br />
&nbsp;&nbsp;"role_name" ,<br />
&nbsp;&nbsp;"text_content" <br />
&nbsp;&nbsp;"emotion_name" <br />
&nbsp;&nbsp;"strength_name"<br />
}
      </code>
        </p>

        <p>
          ➕ 以下标签为 <strong>可选</strong>（根据需要添加，不需要可省略）：
        </p>

        <p>
          <code>
&lt;possible_characters&gt;<br />
{possible_characters}<br />
&lt;/possible_characters&gt;
      </code>
        </p>

        <p>
          <code>
&lt;possible_emotions&gt;<br />
{possible_emotions}<br />
&lt;/possible_emotions&gt;
      </code>
        </p>

        <p>
          <code>
&lt;possible_strengths&gt;<br />
{possible_strengths}<br />
&lt;/possible_strengths&gt;
      </code>
        </p>
      </div>

      <template #footer>
        <el-button type="primary" @click="noticeVisible = false">我已了解</el-button>
      </template>
    </el-dialog>

    <!-- 提示词卡片网格 -->
    <el-row :gutter="20">
      <el-col v-for="item in prompts" :key="item.id" :xs="24" :sm="12" :md="8" :lg="6" style="margin-bottom: 20px;">
        <el-card shadow="hover" class="prompt-card" :body-style="{ padding: '0px' }">
          <!-- 卡片头部 -->
          <div class="card-header">
            <h3 class="prompt-title" :title="item.name">{{ item.name }}</h3>
            <div class="actions">
              <el-button link type="primary" size="small" @click="openDialog(item)">
                <el-icon>
                  <Edit />
                </el-icon>
              </el-button>
              <el-popconfirm title="确定要删除该提示词吗？" @confirm="removePrompt(item)">
                <template #reference>
                  <el-button link type="danger" size="small">
                    <el-icon>
                      <Delete />
                    </el-icon>
                  </el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>

          <div class="card-body">
            <div class="meta-info">
              <el-tag size="small" effect="plain" class="task-tag">{{ item.task }}</el-tag>
            </div>

            <!-- 描述 -->
            <p class="prompt-desc" :title="item.description">{{ item.description || '暂无描述' }}</p>

            <!-- 内容 -->
            <div class="content-preview">
              <p class="prompt-content">{{ item.content }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑提示词' : '新增提示词'" width="800px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="请输入提示词名称" />
        </el-form-item>
        <el-form-item label="任务" prop="task">
          <el-select v-model="form.task" placeholder="请选择任务">
            <el-option v-for="t in tasks" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" placeholder="请输入提示词内容" rows="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePrompt">保存</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { Edit, Delete, QuestionFilled } from "@element-plus/icons-vue"
import { WarningFilled } from "@element-plus/icons-vue"

import {
  fetchPromptList,
  createPrompt,
  updatePrompt,
  deletePrompt,
  fetchAllTasks
} from "../api/prompt"
const noticeVisible = ref(false)
const prompts = ref([])
const search = ref("")
const dialogVisible = ref(false)
const form = ref({ id: null, name: "", description: "", content: "", task: "" })
const tasks = ref([])
// 加载提示词列表
async function loadPrompts() {
  const data = await fetchPromptList()
  if (search.value) {
    prompts.value = data.filter(p => p.name.includes(search.value))
  } else {
    prompts.value = data
  }
}

onMounted(async () => {
  tasks.value = await fetchAllTasks()
  loadPrompts()
})


// 打开对话框（新增 / 编辑）
function openDialog(row) {
  if (row) {
    form.value = { ...row }
  } else {
    form.value = { id: null, name: "", description: "", content: "" }
  }
  dialogVisible.value = true
}

// 保存提示词（新增或更新）
async function savePrompt() {
  if (!form.value.name) {
    ElMessage.warning("名称不能为空")
    return
  }
  try {
    let res
    if (form.value.id) {
      res = await updatePrompt(form.value.id, form.value)
    } else {
      res = await createPrompt(form.value)
    }

    // ✅ 统一根据 code 判断
    if (res.code === 200) {
      ElMessage.success(res.message || "操作成功")
      dialogVisible.value = false
      await loadPrompts()
    } else {
      ElMessage.error(res.message || "操作失败")
    }
  } catch (err) {
    ElMessage.error("操作失败")
    console.error(err)
  }
}

// 删除提示词
function removePrompt(row) {
  ElMessageBox.confirm(`确定要删除提示词「${row.name}」吗？`, "提示", {
    type: "warning"
  })
    .then(async () => {
      try {
        await deletePrompt(row.id)
        ElMessage.success("已删除")
        await loadPrompts()
      } catch (err) {
        ElMessage.error("删除失败")
        console.error(err)
      }
    })
    .catch(() => { })
}
</script>

<style scoped>
/* 顶部标题栏 */
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.page-title {
  font-size: 20px;
  font-weight: bold;
  margin: 0;
}

.toolbar {
  display: flex;
  align-items: center;
}

/* 卡片 */
.prompt-card {
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 100%;
  border: 1px solid #ebeef5;
}

.prompt-card:hover {
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
  border-bottom: 1px solid #f0f2f5;
  background-color: #fafafa;
}

.prompt-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.actions {
  display: flex;
  gap: 8px;
}

.card-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.meta-info {
  display: flex;
  align-items: center;
}

.task-tag {
  border-radius: 4px;
  font-weight: 500;
}

/* 描述 */
.prompt-desc {
  font-size: 13px;
  color: #909399;
  margin: 0;
  line-height: 1.5;
  height: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 内容预览区域 */
.content-preview {
  background-color: #f8f9fa;
  border-radius: 6px;
  padding: 10px;
  border: 1px solid #f0f2f5;
}

.prompt-content {
  font-size: 12px;
  color: #606266;
  margin: 0;
  line-height: 1.6;
  height: 58px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  font-family: monospace;
}

.el-button.is-plain.el-button--danger {
  border: 1px solid #f56c6c;
  /* 红色边框 */
  color: #f56c6c;
  /* 红色文字 */
  background: #fef0f0;
  /* 淡红背景 */
  font-weight: 600;
  transition: all 0.2s ease;
}

.el-button.is-plain.el-button--danger:hover {
  background: #f56c6c;
  /* 红底 */
  color: #fff;
  /* 白字 */
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.3);
}
</style>
