<template>
    <div class="page-wrap">
        <!-- 顶部信息栏 -->
        <div class="header">
            <div class="title-side">
                <el-button text @click="$router.back()">
                    <el-icon>
                        <ArrowLeft />
                    </el-icon> 返回
                </el-button>
                <h2 class="proj-title">{{ project?.name || '项目名称' }}</h2>
                <el-tag effect="plain" type="info">ID: {{ projectId }}</el-tag>
                <el-tag effect="light" class="ml8">章节 {{ stats.chapterCount }}</el-tag>
                <el-tag effect="light" class="ml8">角色 {{ stats.roleCount }}</el-tag>
                <el-tag effect="light" class="ml8">台词 {{ stats.lineCount }}</el-tag>
            </div>
            <div class="action-side">
                <el-button @click="openProjectSettings">
                    <el-icon>
                        <Setting />
                    </el-icon> 项目设置
                </el-button>
                <el-button type="primary" @click="openQueue = true" class="ml8">
                    <el-icon>
                        <Headset />
                    </el-icon> 任务队列
                </el-button>
            </div>
        </div>

        <el-container class="main">
            <!-- 左侧章节 -->
            <el-aside width="240px" class="aside">
                <div class="aside-head">
                    <div class="aside-title">
                        <el-icon>
                            <Menu />
                        </el-icon><span>章节</span>
                    </div>
                    <el-button type="primary" text @click="dialogNewChapter = true">
                        <el-icon>
                            <Plus />
                        </el-icon>
                    </el-button>
                </div>

                <el-input v-model="chapterKeyword" placeholder="搜索章节" clearable class="mb8">
                    <template #prefix><el-icon>
                            <Search />
                        </el-icon></template>
                </el-input>

                <el-scrollbar height="calc(100vh - 210px)">
                    <el-menu :default-active="String(activeChapterId)" class="chapter-menu" @select="onSelectChapter">
                        <el-menu-item v-for="c in filteredChapters" :key="c.id" :index="String(c.id)">
                            <div class="chapter-item">
                                <span class="ellipsis">{{ c.title }}</span>
                                <div class="chapter-ops">
                                    <el-tooltip content="重命名">
                                        <el-button link @click.stop="openRenameChapter(c)"><el-icon>
                                                <Edit />
                                            </el-icon></el-button>
                                    </el-tooltip>
                                    <el-tooltip content="删除">
                                        <el-popconfirm title="确认删除该章节？" @confirm="deleteChapter(c)">
                                            <template #reference>
                                                <el-button link type="danger"><el-icon>
                                                        <Delete />
                                                    </el-icon></el-button>
                                            </template>
                                        </el-popconfirm>
                                    </el-tooltip>
                                </div>
                            </div>
                        </el-menu-item>
                    </el-menu>
                </el-scrollbar>
            </el-aside>

            <!-- 主区域 -->
            <el-container>
                <el-main class="content">
                    <!-- 章节正文 -->
                    <el-card class="chapter-card" shadow="never">
                        <div class="chapter-card-head">
                            <div class="left">
                                <el-icon>
                                    <Document />
                                </el-icon>
                                <span class="title">{{ currentChapter?.title || '未选择章节' }}</span>
                                <el-tag v-if="currentChapterContent" size="small" effect="light" class="ml8">
                                    {{ currentChapterContent.length }} 字
                                </el-tag>
                            </div>
                            <div class="right">
                                <el-button @click="toggleChapterCollapse" text>
                                    <el-icon>
                                        <CaretBottom v-if="!chapterCollapsed" />
                                        <CaretRight v-else />
                                    </el-icon>
                                    {{ chapterCollapsed ? '展开' : '收起' }}
                                </el-button>
                                <el-divider direction="vertical" />
                                <el-button @click="openImportDialog" text>
                                    <el-icon>
                                        <Upload />
                                    </el-icon> 导入/粘贴
                                </el-button>
                                <el-button @click="openEditDialog" text :disabled="!currentChapter">
                                    <el-icon>
                                        <Edit />
                                    </el-icon> 编辑
                                </el-button>
                                <el-button type="primary" @click="splitByLLM" :disabled="!currentChapterContent">
                                    <el-icon>
                                        <MagicStick />
                                    </el-icon> LLM 拆分为台词
                                </el-button>


                                <!-- 新增：导出 Prompt -->
                                <!-- <el-button @click="exportLLMPrompt" :disabled="!currentChapter">
                                    <el-icon>
                                        <Document />
                                    </el-icon> 导出 Prompt
                                </el-button> -->

                                <!-- 新增：导入第三方 JSON -->
                                <!-- <el-button @click="openImportThirdDialog" :disabled="!currentChapter">
                                    <el-icon>
                                        <Upload />
                                    </el-icon> 导入第三方 JSON
                                </el-button> -->
                            </div>
                        </div>

                        <el-collapse-transition>
                            <div v-show="!chapterCollapsed" class="chapter-content-box">
                                <el-empty v-if="!currentChapterContent" description="尚未导入本章节正文，点击右上角『导入/粘贴』" />
                                <el-scrollbar v-else class="chapter-scroll">
                                    <pre class="chapter-text">{{ currentChapterContent }}</pre>
                                </el-scrollbar>
                            </div>
                        </el-collapse-transition>
                    </el-card>

                    <el-tabs v-model="activeTab">
                        <!-- 台词管理 -->
                        <el-tab-pane label="台词管理" name="lines">
                            <div class="toolbar">
                                <el-select v-model="roleFilter" clearable filterable placeholder="按角色筛选" class="w220">
                                    <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
                                </el-select>
                                <el-input v-model="lineKeyword" placeholder="搜索台词文本" clearable class="w300 ml8" />
                                <el-button @click="loadLines" class="ml8">
                                    <el-icon>
                                        <Refresh />
                                    </el-icon> 刷新
                                </el-button>
                                <el-button type="primary" @click="generateAll" class="ml8">
                                    <el-icon>
                                        <Headset />
                                    </el-icon> 批量生成音频
                                </el-button>

                                <el-button type="success" @click="markAllAsCompleted">
                                    <el-icon>
                                        <Check />
                                    </el-icon> 导出配音与字幕
                                </el-button>

                            </div>

                            <el-table :data="displayedLines" border stripe highlight-current-row class="lines-table"
                                :header-cell-style="tableHeaderStyle">

                                <el-table-column prop="line_order" label="序" width="60" align="center"
                                    header-align="center" show-overflow-tooltip />


                                <el-table-column prop="role_id" label="角色" width="150">
                                    <template #header>
                                        <span style="display: flex; align-items: center;">
                                            角色
                                            <el-tooltip :content="roleColumnLocked ? '已锁定，禁止修改' : '点击锁定，防止误操作'"
                                                placement="top">
                                                <el-button :icon="roleColumnLocked ? Lock : Unlock" circle size="small"
                                                    link @click="roleColumnLocked = !roleColumnLocked" />
                                            </el-tooltip>
                                        </span>
                                    </template>

                                    <template #default="{ row }">
                                        <div class="role-cell" style="align-items: flex-start;">
                                            <!-- 角色首字头像 -->
                                            <el-avatar :size="32">{{ getRoleName(row.role_id).slice(0, 1) }}</el-avatar>

                                            <!-- 角色选择下拉 -->
                                            <div class="ml8" style="flex: 1;">
                                                <el-select v-model="row.role_id" filterable clearable placeholder="选择角色"
                                                    class="w-full" size="small" :disabled="roleColumnLocked"
                                                    @change="updateLineRole(row)">
                                                    <el-option v-for="r in roles" :key="r.id" :label="r.name"
                                                        :value="r.id" />
                                                </el-select>

                                                <div class="mt-1" style="font-size: 12px; color: #888;">
                                                    <el-tag size="small" v-if="getRoleVoiceName(row.role_id)">
                                                        {{ getRoleVoiceName(row.role_id) }}
                                                    </el-tag>
                                                    <el-tag size="small" type="info" v-else>未绑定音色</el-tag>
                                                </div>
                                            </div>
                                        </div>
                                    </template>
                                </el-table-column>




                                <el-table-column label="台词文本" min-width="150">
                                    <template #default="{ row }">
                                        <el-input v-model="row.text_content" placeholder="输入台词内容" size="small"
                                            type="textarea" autosize :disabled="textLocked" @blur="updateLineText(row)"
                                            @keyup.enter.native="updateLineText(row)" />
                                    </template>

                                    <!-- 可选：在表头添加锁图标 -->
                                    <template #header>
                                        <span style="display: flex; align-items: center;">
                                            台词文本
                                            <el-tooltip :content="textLocked ? '已锁定，禁止修改' : '点击锁定，防止误操作'"
                                                placement="top">
                                                <el-button :icon="textLocked ? Lock : Unlock" circle size="small" link
                                                    @click="textLocked = !textLocked" />
                                            </el-tooltip>
                                        </span>
                                    </template>
                                </el-table-column>

                                <!-- 情绪 -->
                                <el-table-column label="情绪" width="100">
                                    <template #header>
                                        <span style="display: flex; align-items: center;">
                                            情绪
                                            <el-tooltip :content="emotionLocked ? '已锁定，禁止修改' : '点击锁定，防止误操作'"
                                                placement="top">
                                                <el-button :icon="emotionLocked ? Lock : Unlock" circle size="small"
                                                    link @click="emotionLocked = !emotionLocked" />
                                            </el-tooltip>
                                        </span>
                                    </template>
                                    <template #default="{ row }">
                                        <el-select v-model="row.emotion_id" placeholder="选择情绪" size="small"
                                            :disabled="emotionLocked" @change="updateLineEmotion(row)">
                                            <el-option v-for="opt in emotionOptions" :key="opt.value" :label="opt.label"
                                                :value="opt.value" />
                                        </el-select>
                                    </template>
                                </el-table-column>

                                <!-- 强度 -->
                                <el-table-column label="强度" width="100">
                                    <template #header>
                                        <span style="display: flex; align-items: center;">
                                            强度
                                            <el-tooltip :content="strengthLocked ? '已锁定，禁止修改' : '点击锁定，防止误操作'"
                                                placement="top">
                                                <el-button :icon="strengthLocked ? Lock : Unlock" circle size="small"
                                                    link @click="strengthLocked = !strengthLocked" />
                                            </el-tooltip>
                                        </span>
                                    </template>
                                    <template #default="{ row }">
                                        <el-select v-model="row.strength_id" placeholder="选择强度" size="small"
                                            :disabled="strengthLocked" @change="updateLineStrength(row)">
                                            <el-option v-for="opt in strengthOptions" :key="opt.value"
                                                :label="opt.label" :value="opt.value" />
                                        </el-select>
                                    </template>
                                </el-table-column>



                                <el-table-column label="试听/处理" min-width="320">
                                    <template #default="{ row }">
                                        <div v-if="row.audio_path">
                                            <WaveCellPro :key="waveKey(row)" :src="waveSrc(row)"
                                                :speed="row._procSpeed || 1.0" :volume2x="row._procVolume ?? 1.0"
                                                :start-ms="row.start_ms" :end-ms="row.end_ms" @ready="registerWave"
                                                @request-stop-others="stopOthers" @dispose="unregisterWave"
                                                @confirm="(p) => confirmAndProcess(row, p)" />

                                        </div>
                                        <el-text v-else type="info">无音频</el-text>
                                    </template>
                                </el-table-column>
                                <el-table-column label="#" width="150" align="center">
                                    <template #default="{ row, $index }">

                                        <div style="display: flex; gap: 0px; justify-content: center;">
                                            <el-button size="small" type="primary" plain @click="insertBelow(row)">
                                                插入
                                            </el-button>
                                            <el-popconfirm title="确认删除该台词？" @confirm="deleteLine(row)">
                                                <template #reference>
                                                    <el-button size="small" type="danger" plain>
                                                        删除
                                                    </el-button>
                                                </template>
                                            </el-popconfirm>
                                        </div>
                                    </template>
                                </el-table-column>
                                <el-table-column label="状态" width="100" align="center">
                                    <template #default="{ row }">
                                        <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
                                    </template>
                                </el-table-column>
                                <el-table-column label="操作" width="100" align="center" fixed="right">
                                    <template #default="{ row }">
                                        <el-button size="small" type="primary" :disabled="!canGenerate(row)"
                                            @click="generateOne(row)">生成配音</el-button>
                                        <!-- <el-button size="small" :disabled="!row.audio_path"
                                            @click="playLine(row)">播放</el-button> -->
                                        <!-- 新增：处理音频（变速不变调 + 音量） -->

                                    </template>
                                </el-table-column>


                            </el-table>
                        </el-tab-pane>

                        <!-- 角色库 -->
                        <el-tab-pane label="角色库" name="roles">
                            <div class="toolbar">
                                <el-input v-model="roleKeyword" placeholder="搜索角色" clearable class="w260" />
                                <el-button class="ml8" type="primary" @click="$router.push('/voices')">
                                    <el-icon>
                                        <Plus />
                                    </el-icon> 管理音色库
                                </el-button>
                                <el-button type="success" @click="openCreateRole">
                                    <el-icon>
                                        <Plus />
                                    </el-icon> 新建角色
                                </el-button>

                            </div>

                            <div class="role-grid">
                                <el-card v-for="r in displayedRoles" :key="r.id" class="role-card" shadow="hover">
                                    <!-- src/views/YourView.vue，角色卡片组件中 -->
                                    <div class="role-card-head">
                                        <el-avatar :size="40">{{ r.name.slice(0, 1) }}</el-avatar>
                                        <div class="role-meta">
                                            <div class="role-title">{{ r.name }}</div>
                                            <div class="role-desc ellipsis-2">{{ r.description || '—' }}</div>
                                        </div>
                                        <!-- 新增：操作按钮 -->
                                        <div class="role-actions">
                                            <el-tooltip content="重命名">
                                                <el-button link @click="openRenameRole(r)">
                                                    <el-icon>
                                                        <Edit />
                                                    </el-icon>
                                                </el-button>
                                            </el-tooltip>
                                            <el-tooltip content="删除">
                                                <el-popconfirm title="确定删除该角色？" @confirm="deleteRole(r)">
                                                    <template #reference>
                                                        <el-button link type="danger"><el-icon>
                                                                <Delete />
                                                            </el-icon></el-button>
                                                    </template>
                                                </el-popconfirm>
                                            </el-tooltip>
                                        </div>
                                    </div>


                                    <div class="bind-row">
                                        <!-- 左边：标签 + 试听 -->
                                        <div class="bind-left">
                                            <el-tag v-if="getRoleVoiceName(r.id)" type="danger">
                                                {{ getRoleVoiceName(r.id) }}
                                            </el-tag>
                                            <el-tag v-else type="info">未绑定音色</el-tag>

                                            <el-button
  circle
  plain
  :disabled="!roleVoiceMap[r.id]"
  @click="toggleVoicePlay(roleVoiceMap[r.id])"
  :title="isPlaying && currentVoiceId === roleVoiceMap[r.id] ? '暂停' : '试听音色'"
>
  <el-icon>
    <Headset />
  </el-icon>
</el-button>

                                        </div>

                                        <!-- 右边：选择音色 -->
                                        <div class="bind-right">
                                            <el-button :type="getRoleVoiceName(r.id) ? 'primary' : 'danger'"
                                                size="small" @click="openVoiceDialog(r)">
                                                {{ getRoleVoiceName(r.id) ? '更换音色' : '绑定音色' }}
                                            </el-button>

                                        </div>
                                    </div>


                                </el-card>
                            </div>
                        </el-tab-pane>
                    </el-tabs>
                </el-main>
            </el-container>
        </el-container>

        <!-- 右侧任务队列 -->
        <el-drawer v-model="openQueue" title="任务队列" size="420px">
            <el-timeline>
                <el-timeline-item v-for="q in queue" :key="q.id" :timestamp="q.time" :type="q.type">
                    <div class="queue-item">
                        <div class="queue-title">{{ q.title }}</div>
                        <div class="queue-meta">{{ q.meta }}</div>
                    </div>
                </el-timeline-item>
            </el-timeline>
        </el-drawer>

        <!-- 新建章节 -->
        <el-dialog title="新建章节" v-model="dialogNewChapter" width="460px">
            <el-form :model="chapterForm" ref="chapterFormRef" label-width="90px">
                <el-form-item label="章节标题" prop="title"
                    :rules="[{ required: true, message: '请输入章节标题', trigger: 'blur' }]">
                    <el-input v-model="chapterForm.title" placeholder="例如：第一章 初遇" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="dialogNewChapter = false">取消</el-button>
                <el-button type="primary" @click="createChapter">确定</el-button>
            </template>
        </el-dialog>

        <!-- 重命名章节 -->
        <el-dialog title="重命名章节" v-model="dialogRenameChapter" width="460px">
            <el-form :model="chapterForm" ref="chapterRenameRef" label-width="90px">
                <el-form-item label="新标题" prop="title"
                    :rules="[{ required: true, message: '请输入新标题', trigger: 'blur' }]">
                    <el-input v-model="chapterForm.title" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="dialogRenameChapter = false">取消</el-button>
                <el-button type="primary" @click="renameChapter">确定</el-button>
            </template>
        </el-dialog>

        <!-- 导入/粘贴正文 -->
        <el-dialog title="导入/粘贴章节正文" v-model="dialogImport" width="720px">
            <el-input v-model="importText" type="textarea" :rows="14" placeholder="在此处粘贴本章节全文…" />
            <template #footer>
                <el-button @click="dialogImport = false">取消</el-button>
                <el-button type="primary" @click="submitImport">保存</el-button>
            </template>
        </el-dialog>

        <!-- 编辑正文 -->
        <el-dialog title="编辑章节正文" v-model="dialogEdit" width="720px">
            <el-input v-model="editText" type="textarea" :rows="14" placeholder="编辑本章节全文…" />
            <template #footer>
                <el-button @click="dialogEdit = false">取消</el-button>
                <el-button type="primary" @click="submitEdit">保存</el-button>
            </template>
        </el-dialog>
        <!-- 角色重命名弹窗 -->
        <el-dialog title="重命名角色" v-model="dialogRenameRole" width="400px">
            <el-form :model="roleForm" label-width="80px">
                <el-form-item label="角色名称" prop="name"
                    :rules="[{ required: true, message: '请输入角色名称', trigger: 'blur' }]">
                    <el-input v-model="roleForm.name" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="dialogRenameRole = false">取消</el-button>
                <el-button type="primary" @click="renameRole">确定</el-button>
            </template>
        </el-dialog>
        <!-- 新建角色 -->
        <el-dialog title="新建角色" v-model="dialogCreateRole" width="460px">
            <el-form :model="createRoleForm" ref="createRoleFormRef" label-width="88px">
                <el-form-item label="角色名称" prop="name"
                    :rules="[{ required: true, message: '请输入角色名称', trigger: 'blur' }]">
                    <el-input v-model="createRoleForm.name" placeholder="如：路人甲 / 萧炎" />
                </el-form-item>

                <el-form-item label="角色描述">
                    <el-input v-model="createRoleForm.description" placeholder="可选：角色备注" />
                </el-form-item>

                <el-form-item label="默认音色">
                    <el-select v-model="createRoleForm.default_voice_id" filterable clearable placeholder="可选">
                        <el-option v-for="v in voicesOptions" :key="v.id" :label="v.name" :value="v.id" />
                    </el-select>
                </el-form-item>
            </el-form>

            <template #footer>
                <el-button @click="dialogCreateRole = false">取消</el-button>
                <el-button type="primary" @click="createRole">创建</el-button>
            </template>
        </el-dialog>
        <!-- 项目设置弹窗（复用创建项目表单结构） -->
        <el-dialog v-model="settingsVisible" title="项目设置" width="500px">
            <el-form :model="settingsForm" :rules="settingsRules" ref="settingsFormRef" label-width="100px">
                <!-- 项目名称 -->
                <el-form-item label="项目名称" prop="name">
                    <el-input v-model="settingsForm.name" placeholder="请输入项目名称"></el-input>
                </el-form-item>

                <!-- 项目描述 -->
                <el-form-item label="项目描述" prop="description">
                    <el-input v-model="settingsForm.description" type="textarea" placeholder="请输入项目描述"
                        :rows="3"></el-input>
                </el-form-item>

                <!-- LLM 提供商 -->
                <el-form-item label="LLM 提供商">
                    <el-select v-model="settingsForm.llm_provider_id" placeholder="请选择 LLM 提供商" clearable
                        style="width: 100%;">
                        <el-option v-for="provider in llmProviders" :key="provider.id" :label="provider.name"
                            :value="provider.id" />
                    </el-select>
                </el-form-item>

                <!-- LLM 模型 -->
                <el-form-item label="LLM 模型">
                    <el-select v-model="settingsForm.llm_model" placeholder="请选择 LLM 模型" clearable style="width: 100%;">
                        <el-option v-for="model in availableModels" :key="model" :label="model" :value="model" />
                    </el-select>
                    <!-- 如果为空就提示 -->
                <div v-if="!settingsForm.llm_model && settingsForm.llm_provider_id" style="color: #f56c6c; font-size: 12px; margin-top: 4px;">
                    请选择 LLM 模型
                </div>
                </el-form-item>

                <!-- TTS 提供商 -->
                <el-form-item label="TTS 引擎">
                    <el-select v-model="settingsForm.tts_provider_id" placeholder="请选择 TTS 引擎" clearable
                        style="width: 100%;">
                        <el-option v-for="tts in ttsProviders" :key="tts.id" :label="tts.name" :value="tts.id" />
                    </el-select>
                </el-form-item>
                <!-- 提示词模板 -->
                <el-form-item label="提示词模版">
                    <el-select v-model="settingsForm.prompt_id" placeholder="请选择提示词" clearable filterable>
                        <el-option
                        v-for="p in prompts"
                        :key="p.id"
                        :label="p.name"  
                        :value="p.id"
                        />
                    </el-select>
                    </el-form-item>
            </el-form>

            <template #footer>
                <el-button @click="settingsVisible = false">取消</el-button>
                <el-button type="primary" :loading="savingSettings" @click="saveProjectSettings">确定</el-button>
            </template>
        </el-dialog>

        <!-- 导入第三方 JSON（台词） -->
        <el-dialog title="导入第三方 JSON（台词）" v-model="dialogImportThird" width="720px">
            <el-alert type="info" :closable="false" class="mb-2"
                title="请粘贴一个 JSON 数组，每个元素形如 { role_name: string, text_content: string }；提交后将直接写入该章节台词。" />
            <el-input v-model="thirdJsonText" type="textarea" :rows="14"
                placeholder='[{"role_name":"旁白","text_content":"……"}]' />
            <div class="flex items-center gap-2 mt-2">
                <el-upload :show-file-list="false" accept=".json,application/json" :before-upload="readThirdJsonFile">
                    <el-button>从文件加载 .json</el-button>
                </el-upload>
                <el-text type="info">（可选）选择本地 JSON 文件自动填充</el-text>
            </div>
            <template #footer>
                <el-button @click="dialogImportThird = false">取消</el-button>
                <el-button type="primary" @click="submitImportThird">导入</el-button>
            </template>
        </el-dialog>

        <el-dialog v-model="dialogSelectVoice.visible" title="选择音色" width="720px">
            <div class="voice-grid">
                <el-card v-for="v in voicesOptions" :key="v.id" class="voice-card" shadow="hover"
                    @click="selectVoice(v)">
                    <div class="voice-card-head">
                        <div class="voice-title">{{ v.name }}</div>
                        <div class="voice-desc">{{ v.description || '无描述' }}</div>
                    </div>
                    <div class="voice-actions">
                        <el-button
  circle
  @click.stop="toggleVoicePlay(v.id)"
  :title="isPlaying && currentVoiceId === v.id ? '暂停' : '试听'"
>
  <el-icon>
    <Headset />
  </el-icon>
</el-button>

                        <el-button type="primary" size="small" @click.stop="confirmSelectVoice(v)">
                            选择
                        </el-button>
                    </div>
                </el-card>
            </div>
        </el-dialog>

        <!-- 拆分预览（解析 get-lines 的结果） -->
        <!-- <el-dialog title="拆分预览" v-model="dialogSplitPreview" width="780px">
            <el-table :data="splitPreview" border stripe>
                <el-table-column prop="role_name" label="角色" width="180" />
                <el-table-column prop="text_content" label="台词" />
            </el-table>
            <template #footer>
                <el-button @click="dialogSplitPreview = false">取消</el-button>
                <el-button type="primary" @click="confirmSaveInitLines">保存为初始台词</el-button>
            </template>
        </el-dialog> -->
    </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, Unlock, ArrowLeft, Setting, Headset, Menu, Plus, Search, Edit, Delete, Refresh, MagicStick, Document, CaretBottom, CaretRight, Upload, VideoPlay, VideoPause, Check } from '@element-plus/icons-vue'
import service from '../api/config'
import * as chapterAPI from '../api/chapter'
import * as roleAPI from '../api/role'
import * as projectAPI from '../api/project'
import * as lineAPI from '../api/line'
import * as voiceAPI from '../api/voice'
import * as providerAPI from '../api/provider'
import * as enumAPI from '../api/enums' // 例如 emotion/strength API
import * as promptAPI from '../api/prompt'


const emotionLocked = ref(false)
const strengthLocked = ref(false)

const roleColumnLocked = ref(false)
// //////////////////////////////////websocket
// ---- WebSocket（局部，纯 JS）+ 任务队列 ----
import { onUnmounted } from 'vue'

let ws = null
let wsRetry = 0
let reconnectTimer = null

function wsUrl() {
    const httpBase = service.defaults.baseURL // 例如 'http://127.0.0.1:8000/'
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const host = httpBase.replace(/^http(s?):\/\//, '').replace(/\/$/, '') // 去掉 http:// 和末尾斜杠
    return `${proto}://${host}/ws?project_id=${projectId}`
}

// 队列：追加一条并持久化（最多保留 200 条）
function addQueue(item) {
    queue.value.unshift({
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        time: new Date().toLocaleTimeString(),
        title: item.title || '',
        meta: item.meta || '',
        type: item.type || 'info', // ElementPlus: primary/success/warning/danger/info
    })
    if (queue.value.length > 200) queue.value.length = 200
    try { localStorage.setItem(`queue_${projectId}`, JSON.stringify(queue.value)) } catch { }
}
function restoreQueue() {
    try {
        const raw = localStorage.getItem(`queue_${projectId}`)
        if (raw) queue.value = JSON.parse(raw)
    } catch { }
}

// 根据后端推送更新本地行
function applyLineUpdate(msg) {
    const { line_id, status, audio_path } = msg
    const idx = lines.value.findIndex(l => l.id === line_id)
    if (idx >= 0) {
        const old = lines.value[idx]
        lines.value[idx] = {
            ...old,
            status,                                  // 'pending' | 'processing' | 'done' | 'failed'
            audio_path: audio_path ?? old.audio_path // 若推送里没有就保留原值
        }
        // ✅ 关键：当生成完成或路径发生变化时，强制重载对应 WaveCellPro
        if (status === 'done' || pathChanged) {
            bumpVer(line_id)           // 让 :key 与 :src?v= 都变
        }
    } else {
        // 当前章节列表里没有该行（例如切换了章节），这里先忽略。
        // 需要的话也可以触发一次局部刷新：activeChapterId.value && loadLines()
    }
}

const HEARTBEAT_INTERVAL = 60000;   // 60s 发送一次 ping，正常来说一般15s
const HEARTBEAT_DEADLINE = 7000;   // 7s 内未收到 pong 视为假死
let heartbeatTimer = null;     // 定时发送 ping
let heartbeatTimeout = null;   // 等待 pong 的超时
function startHeartbeat() {
    // 周期性发送 ping
    heartbeatTimer = setInterval(() => {
        // 如果 readyState 不是 OPEN，等 onclose 去处理重连
        if (!ws || ws.readyState !== WebSocket.OPEN) return;

        // 发送应用层 ping，并启动一个等待 pong 的超时定时器
        try {
            ws.send(JSON.stringify({ type: 'ping', ts: Date.now() }));
            // addQueue({ title: '心跳发送ping', meta: '心跳机制', type: 'info' });
        } catch { }
        if (heartbeatTimeout) clearTimeout(heartbeatTimeout);
        heartbeatTimeout = setTimeout(() => {
            // 未按期收到 pong，判定为假死，主动关闭触发重连
            addQueue({ title: '心跳超时', meta: '触发重连', type: 'warning' });
            try { ws && ws.close(); } catch { }
        }, HEARTBEAT_DEADLINE);
    }, HEARTBEAT_INTERVAL);
}

function connectWS() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return

    ws = new WebSocket(wsUrl())

    ws.onopen = () => {
        wsRetry = 0
        addQueue({ title: '已连接任务通道', meta: `项目 ${projectId}`, type: 'primary' })
        // 启动心跳
        startHeartbeat();
        // 可选：连接后拉一次你后端的“快照”接口，补齐中途错过的状态（若有）
        // try { request.get(`/chapters/processing/${projectId}`).then(res => { if (res?.code === 200) res.data.forEach(applyLineUpdate) }) } catch {}
    }

    ws.onmessage = (evt) => {
        try {
            const msg = JSON.parse(evt.data)
            if (msg.type === 'pong') {
                if (heartbeatTimeout) { clearTimeout(heartbeatTimeout); heartbeatTimeout = null; }
                // addQueue({ title: '心跳收到pong', meta: '连接正常', type: 'info' });
                return;
            }
            if (msg.event === 'line_update') {
                applyLineUpdate(msg)

                // 队列可视化
                const type = msg.status === 'failed' ? 'danger'
                    : msg.status === 'processing' ? 'warning'
                        : msg.status === 'done' ? 'success'
                            : 'info'
                const meta = msg.meta || (msg.status === 'done'
                    ? '生成完成'
                    : msg.status === 'processing'
                        ? '生成中'
                        : msg.status === 'failed'
                            ? '生成失败'
                            : '状态更新')
                addQueue({ title: `台词 #${msg.line_id}`, meta, type })
            }
        } catch { /* 忽略解析错误 */ }
    }

    ws.onclose = () => {
        const delay = Math.min(1000 * Math.pow(2, wsRetry++), 15000)
        addQueue({ title: '任务通道已断开', meta: `将于 ${delay}ms 后重连`, type: 'warning' })
        reconnectTimer = setTimeout(connectWS, delay)
    }

    ws.onerror = () => {
        try { ws && ws.close() } catch { }
    }
}


// //////////////////////////////////websocket
// @ts-ignore
const native = window.native

// 路由参数
const route = useRoute()
const projectId = Number(route.params.id)

// 顶部
const project = ref(null)
const stats = ref({ chapterCount: 0, roleCount: 0, lineCount: 0 })
// —— 项目设置（复用“创建项目”表单结构）——
const settingsVisible = ref(false)
const savingSettings = ref(false)
const settingsFormRef = ref(null)
const settingsForm = ref({
    name: '',
    description: '',
    llm_provider_id: null,
    llm_model: null,
    tts_provider_id: null,
    prompt_id: null
})
const settingsRules = {
    name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
    description: [{ required: true, message: '请输入项目描述', trigger: 'blur' }],
    llm_model: [{ required: true, message: '请选择 LLM 模型', trigger: 'change' }],
}

// Provider 下拉
const llmProviders = ref([])
const availableModels = ref([])
const ttsProviders = ref([])
const prompts = ref([])

// 打开“项目设置”弹窗：预填现有项目数据 + 拉取 Provider
async function openProjectSettings() {

    console.log('项目详情', project.value)
    // 获取项目详情

    settingsVisible.value = true
    // 先把当前项目的字段填进去（你已有 project 对象）
    settingsForm.value = {
        name: project.value?.name || '',
        description: project.value?.description || '',
        llm_provider_id: project.value?.llmProviderId ?? project.value?.llm_provider_id ?? null,
        llm_model: project.value?.llmModel ?? project.value?.llm_model ?? null,
        tts_provider_id: project.value?.ttsProviderId ?? project.value?.tts_provider_id ?? null,
        prompt_id: project.value?.promptId ?? project.value?.prompt_id ?? null
    }
    console.log('表格详情', settingsForm.value)

    // 并行拉取 Provider
    try {
        const [llmRes, ttsRes, promptRes] = await Promise.all([providerAPI.fetchLLMProviders(), providerAPI.fetchTTSProviders(), promptAPI.fetchPromptList()])
        llmProviders.value = llmRes || []
        ttsProviders.value = ttsRes || []
        prompts.value = promptRes || []   // ✅ 保存提示词列表
        console.log('提示词列表', promptRes)
        // 回填模型列表
        const provider = llmProviders.value.find(p => p.id === settingsForm.value.llm_provider_id)
        console.log('模型列表', provider)
        // 将provider.model_list转为数组
        availableModels.value = provider ? (provider.model_list ? provider.model_list.split(',') : []) : []
        // 如果当前选的模型不在列表里，清空
        if (!availableModels.value.includes(settingsForm.value.llm_model)) {
            settingsForm.value.llm_model = null
        }

    } catch (e) {
        // 忽略错误，用空列表
        llmProviders.value = []
        ttsProviders.value = []
        availableModels.value = []
        prompts.value = []
    }
}
watch(
  () => settingsForm.value.llm_provider_id,
  (newProviderId, oldProviderId) => {
    // 如果是初始化（oldProviderId === undefined/null），不要清空
    if (!oldProviderId) {
      const provider = llmProviders.value.find(p => p.id === newProviderId)
      availableModels.value = provider ? (provider.model_list ? provider.model_list.split(',') : []) : []
      return
    }

    // 只有用户真的切换时才清空
    settingsForm.value.llm_model = null
    const provider = llmProviders.value.find(p => p.id === newProviderId)
    availableModels.value = provider ? (provider.model_list ? provider.model_list.split(',') : []) : []
  }
)


// 保存=更新项目（直接调用你的 update 接口）
async function saveProjectSettings() {
    console.log('保存项目设置', settingsForm.value)
    if (!projectId) return

    try {
        // await new Promise((resolve, reject) => {
        //   settingsFormRef.value.validate((valid) => (valid ? resolve() : reject()))
        // })

        // 仅提交需要的字段；与后端 DTO 对齐
        const payload = {
            name: settingsForm.value.name,
            description: settingsForm.value.description,
            llm_provider_id: settingsForm.value.llm_provider_id,
            llm_model: settingsForm.value.llm_model,
            tts_provider_id: settingsForm.value.tts_provider_id,
            prompt_id: settingsForm.value.prompt_id
        }
        console.log('保存项目设置结果', projectId)

        const res = await projectAPI.updateProject(projectId, payload)
        console.log('保存项目设置结果', res)
        if (res?.code === 200) {
            ElMessage.success('项目设置已保存')
            settingsVisible.value = false
            await loadProject() // 刷新头部显示的项目名等
        } else {
            ElMessage.error(res?.message || '保存失败')
        }
    } catch {
        /* 校验失败或异常 */
    } finally {
        savingSettings.value = false
    }
}


// 章节
const chapters = ref([]) // ChapterResponseDTO[]
const activeChapterId = ref(null)
const chapterKeyword = ref('')
const filteredChapters = computed(() => {
    const kw = chapterKeyword.value.trim().toLowerCase()
    return chapters.value.filter(c => c.title.toLowerCase().includes(kw))
})
const currentChapter = computed(() => chapters.value.find(c => c.id === activeChapterId.value) || null)
const currentChapterContent = computed(() => currentChapter.value?.text_content || '')

const chapterCollapsed = ref(true)
function toggleChapterCollapse() { chapterCollapsed.value = !chapterCollapsed.value }

async function loadProject() {
    const res = await projectAPI.getProjectDetail(projectId)
    if (res?.code === 200) project.value = res.data
}

async function loadChapters() {
    const res = await chapterAPI.getChaptersByProject(projectId)
    chapters.value = res?.code === 200 ? (res.data || []) : []
    stats.value.chapterCount = chapters.value.length
    if (!activeChapterId.value && chapters.value[0]) {
        activeChapterId.value = chapters.value[0].id
        await loadLines()
        await loadChapterDetail(activeChapterId.value)
    }
}

async function loadChapterDetail(chapterId) {
    const res = await chapterAPI.getChapterDetail(chapterId)
    if (res?.code === 200) {
        // 更新该章在列表里的 text_content
        const idx = chapters.value.findIndex(c => c.id === chapterId)
        if (idx >= 0) chapters.value[idx] = res.data
    }
}

function onSelectChapter(indexStr) {
    activeChapterId.value = Number(indexStr)
    loadLines()
    loadChapterDetail(activeChapterId.value)
}

const dialogNewChapter = ref(false)
const dialogRenameChapter = ref(false)
const chapterForm = ref({ id: null, title: '' })

async function createChapter() {
    const title = chapterForm.value.title?.trim()
    if (!title) return
    const res = await chapterAPI.createChapter(title, projectId)
    if (res?.code === 200) {
        ElMessage.success('已创建章节')
        dialogNewChapter.value = false
        chapterForm.value = { id: null, title: '' }
        await loadChapters()
    }
}

function openRenameChapter(c) {
    chapterForm.value = { id: c.id, title: c.title }
    dialogRenameChapter.value = true
}

async function renameChapter() {
    const title = chapterForm.value.title?.trim()
    if (!title) return
    const id = chapterForm.value.id
    const payload = { title, project_id: projectId } // DTO 要求必须含 project_id
    // 保持原排序和已有内容（后端允许的话可只传必填字段）
    const exist = chapters.value.find(c => c.id === id)
    if (exist?.text_content) payload.text_content = exist.text_content
    if (exist?.order_index != null) payload.order_index = exist.order_index

    const res = await chapterAPI.updateChapter(id, payload)
    if (res?.code === 200) {
        ElMessage.success('已重命名')
        dialogRenameChapter.value = false
        await loadChapters()
    }
}

async function deleteChapter(c) {
    const res = await chapterAPI.deleteChapter(c.id)
    if (res?.code === 200) {
        ElMessage.success('已删除章节')
        await loadChapters()
        if (activeChapterId.value === c.id && chapters.value[0]) {
            activeChapterId.value = chapters.value[0].id
            await loadLines()
            await loadChapterDetail(activeChapterId.value)
        }
    }
}

// 导入/编辑章节正文
const dialogImport = ref(false)
const dialogEdit = ref(false)
const importText = ref('')
const editText = ref('')

function openImportDialog() {
    importText.value = ''
    dialogImport.value = true
}
function openEditDialog() {
    editText.value = currentChapterContent.value || ''
    dialogEdit.value = true
}

async function submitImport() {
    if (!activeChapterId.value) return
    console.log('导入章节正文')
    const text = importText.value
    console.log('导入章节正文', text)
    const exist = chapters.value.find(c => c.id === activeChapterId.value)
    const payload = {
        title: exist?.title || '未命名章节',
        project_id: projectId,
        text_content: text
    }
    const res = await chapterAPI.updateChapter(activeChapterId.value, payload)
    if (res?.code === 200) {
        ElMessage.success('已导入章节正文')
        dialogImport.value = false
        await loadChapterDetail(activeChapterId.value)
    }
}

async function submitEdit() {
    if (!activeChapterId.value) return
    const text = editText.value
    const exist = chapters.value.find(c => c.id === activeChapterId.value)
    const payload = {
        title: exist?.title || '未命名章节',
        project_id: projectId,
        text_content: text
    }
    const res = await chapterAPI.updateChapter(activeChapterId.value, payload)
    if (res?.code === 200) {
        ElMessage.success('已保存修改')
        dialogEdit.value = false
        await loadChapterDetail(activeChapterId.value)
    }
}

// LLM 拆分（解析 → 预览 → 保存为初始台词）
// const dialogSplitPreview = ref(false)
// const splitPreview = ref([]) // LineInitDTO[]
import { ElLoading, ElMessageBox } from 'element-plus'
async function splitByLLM() {
    if (!activeChapterId.value) return

    try {
        await ElMessageBox.confirm(
            '确定要调用 LLM 对该章节进行台词拆分吗？此操作可能覆盖原有台词。',
            '确认操作',
            {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning',
            }
        )
    } catch {
        // 用户点取消，直接返回
        return
    }
    // 先删除原有台词
    const res = await lineAPI.deleteLinesByChapter(activeChapterId.value)
    if (res?.code === 200) {
        ElMessage.success('已删除原有台词')
        await loadLines()
        await loadRoles()
    } else {
        ElMessage.error(res?.message || '删除原有台词失败')
        return
    }

    const loading = ElLoading.service({
        lock: true,
        text: '正在调用 LLM 拆分台词，请稍候...',
        background: 'rgba(0, 0, 0, 0.4)',
    })

    try {
        console.log('llm进行台词拆分请求开始', projectId, activeChapterId.value)
        const res = await chapterAPI.splitChapterByLLM(projectId, activeChapterId.value)
        if (res?.code === 200) {
            console.log('llm进行台词拆分请求结果 typeof=', typeof res.data, res.data)
            await loadLines()
            await loadRoles()
        } else {
            ElMessage.warning(res?.message || '解析失败')
        }
    } catch (err) {
        ElMessage.error('LLM 拆分台词失败，请稍后再试')
        console.error('LLM 请求失败:', err)
    } finally {
        loading.close()
    }
}

// async function confirmSaveInitLines() {
//     if (!splitPreview.value.length) return
//     const res = await request.post(`/chapters/save-init-lines/${projectId}/${activeChapterId.value}`, splitPreview.value)
//     if (res?.code === 200) {
//         ElMessage.success('已保存初始台词')
//         // dialogSplitPreview.value = false
//         await loadLines()
//         await loadRoles()
//     } else {
//         ElMessage.error(res?.message || '保存失败')
//     }
// }

// 台词列表
const lines = ref([]) // LineResponseDTO[]
const activeTab = ref('lines')
const lineKeyword = ref('')
const roleFilter = ref(null)

const displayedLines = computed(() => {
    const kw = lineKeyword.value.trim().toLowerCase()
    return lines.value
        .filter(l => (!roleFilter.value ? true : l.role_id === roleFilter.value))
        .filter(l => (l.text_content || '').toLowerCase().includes(kw))
})

function tableHeaderStyle() { return { background: '#f7f8fa', fontWeight: 600, color: '#303133' } }




async function loadLines() {
    if (!activeChapterId.value) return
    const res = await lineAPI.getLinesByChapter(activeChapterId.value)
    lines.value = res?.code === 200 ? (res.data || []) : []
    // 音频默认参数：
    stats.value.lineCount = lines.value.length
    // ✅ 关键：当生成完成或路径发生变化时，强制重载对应 WaveCellPro

}

// async function doProcess(row) {
//     if (!row?.id || !row.audio_path) return ElMessage.warning('该行无音频')
//     try {
//         const payload = {
//             speed: Number(row._procSpeed || 1.0),
//             volume: Number(row._procVolume || 1.0),
//         }
//         const res = await lineAPI.processAudio(row.id, payload)
//         if (res?.code === 200) {
//             ElMessage.success('处理完成')
//             // 若另存，后端已更新 audio_path；这里刷新一次列表以拿到最新路径
//             await loadLines()
//             // 可选：自动播放预览
//             // playLine(row)
//         } else {
//             ElMessage.error(res?.message || '处理失败')
//         }
//     } catch (e) {
//         ElMessage.error('处理失败')
//         console.error(e)
//     }
// }

// 替换原来的两个函数
function statusType(s) {
    if (s === 'done') return 'success'
    if (s === 'processing') return 'warning'
    if (s === 'failed') return 'danger'
    return 'info' // pending
}
function statusText(s) {
    if (s === 'done') return '已生成'
    if (s === 'processing') return '生成中'
    if (s === 'failed') return '生成失败'
    return '未生成' // pending
}


function canGenerate(row) {
    const voiceId = getRoleVoiceId(row.role_id)
    // return !!voiceId && row.status !== 'processing'
    return !!voiceId
}

async function generateOne(row) {
    if (!canGenerate(row)) {
        ElMessage.warning('请先为该角色绑定音色')
        return
    }

    // 乐观更新：立即置为 processing，等待 WS 回写最终状态
    // row.status = 'processing'
    addQueue({ title: `台词 #${row.id}`, meta: '已入队，开始生成', type: 'info' })

    const body = {
        chapter_id: row.chapter_id,
        role_id: row.role_id,
        voice_id: getRoleVoiceId(row.role_id),
        id: row.id,
        emotion_id: row.emotion_id,
        strength_id: row.strength_id,
        text_content: row.text_content,
        audio_path: row.audio_path
    }
    console.log(body)
    const res = await lineAPI.generateAudio(projectId, activeChapterId.value, body)
    if (res?.code === 200) {
        ElMessage.success('已添加到异步任务中')
        // 等待 WebSocket 推送来更新为 done/failed
        row.status = 'processing'
    } else {
        row.status = 'failed'
        addQueue({ title: `台词 #${row.id}`, meta: res?.message || '生成失败（请求失败）', type: 'danger' })
        ElMessage.error(res?.message || '生成失败')
    }
}


function generateAll() {
    const todo = displayedLines.value.filter(l => canGenerate(l))
    if (!todo.length) {
        return ElMessage.info('无可生成项或未绑定音色')
    }

    ElMessageBox.confirm(
        '此操作将会重新生成全部已绑定音色的台词，是否继续？',
        '提示',
        {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning',
        }
    )
        .then(() => {
            // 用户确认
            todo.forEach(generateOne)
        })
        .catch(() => {
            // 用户取消
            ElMessage.info('已取消批量生成')
        })
}

// 播放
const audioPlayer = new Audio()

const isPlaying = ref(false)
const currentVoiceId = ref(null)

function toggleVoicePlay(voiceId) {
  if (!voiceId) return
  const voice = voicesOptions.value.find(v => v.id === voiceId)
  if (!voice?.reference_path) return ElMessage.warning('该音色未设置参考音频')

  const src = native?.pathToFileUrl ? native.pathToFileUrl(voice.reference_path) : voice.reference_path

  if (currentVoiceId.value === voiceId) {
    // 切换暂停/继续
    if (isPlaying.value) {
      audioPlayer.pause()
    } else {
      audioPlayer.play().catch(() => ElMessage.error('无法播放音频'))
    }
    return
  }

  // 播放新的音色
  audioPlayer.pause()
  audioPlayer.src = src
  audioPlayer.currentTime = 0
  currentVoiceId.value = voiceId
  audioPlayer.play().catch(() => ElMessage.error('无法播放音频'))
}

// 状态监听
audioPlayer.addEventListener('play', () => { isPlaying.value = true })
audioPlayer.addEventListener('pause', () => { isPlaying.value = false })
audioPlayer.addEventListener('ended', () => {
  isPlaying.value = false
  currentVoiceId.value = null
})



function playLine(row) {
    if (!row.audio_path) return
    try {
        const src = native?.pathToFileUrl ? native.pathToFileUrl(row.audio_path) : row.audio_path
        audioPlayer.pause()
        audioPlayer.src = src
        audioPlayer.currentTime = 0
        audioPlayer.play().catch(() => ElMessage.error('无法播放音频'))
    } catch {
        ElMessage.error('无法播放音频')
    }
}

// 角色 & 绑定音色
const roles = ref([]) // RoleResponseDTO[]
const roleKeyword = ref('')
const displayedRoles = computed(() => {
    const kw = roleKeyword.value.trim().toLowerCase()
    return roles.value.filter(r => r.name.toLowerCase().includes(kw))
})

const roleVoiceMap = ref({}) // roleId -> voiceId
const voicesOptions = ref([]) // VoiceResponseDTO[]

async function loadRoles() {
    const res = await roleAPI.getRolesByProject(projectId)
    roles.value = res?.code === 200 ? (res.data || []) : []
    stats.value.roleCount = roles.value.length
    // 同步默认绑定
    const map = {}
    roles.value.forEach(r => {
        if (r.default_voice_id) map[r.id] = r.default_voice_id
    })
    roleVoiceMap.value = map
}

async function loadVoices() {
    // 默认 TTS = 1
    const res = await voiceAPI.getVoicesByTTS()
    console.log('loadVoices', res)
    voicesOptions.value = res?.code === 200 ? (res.data || []) : []
}

function getRoleName(roleId) { return roles.value.find(r => r.id === roleId)?.name || '—' }
function getRoleVoiceId(roleId) { return roleVoiceMap.value[roleId] || null }
function getRoleVoiceName(roleId) {
    const vid = getRoleVoiceId(roleId)
    return voicesOptions.value.find(v => v.id === vid)?.name
}

async function bindVoice(r) {
    // 更新角色的 default_voice_id
    const payload = {
        name: r.name,
        project_id: r.project_id,
        default_voice_id: roleVoiceMap.value[r.id] || null
    }
    const res = await roleAPI.updateRole(r.id, payload)
    if (res?.code === 200) {
        ElMessage.success(`已为「${r.name}」绑定音色`)
    } else {
        ElMessage.error(res?.message || '绑定失败')
    }
}

// 任务队列（简单示意）
const openQueue = ref(false)
const queue = ref([])

// 初始化

onMounted(async () => {
    await loadProject()
    await Promise.all([loadChapters(), loadRoles(), loadVoices()])

    // —— WebSocket：恢复历史队列并连接
    restoreQueue()
    connectWS()
})

onUnmounted(() => {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    try { ws && ws.close() } catch { }
    ws = null
})


const dialogRenameRole = ref(false)
const roleForm = ref({ id: null, name: '', project_id: projectId })

function openRenameRole(r) {
    roleForm.value = { id: r.id, name: r.name, project_id: r.project_id }
    dialogRenameRole.value = true
}

async function renameRole() {
    const res = await roleAPI.updateRole(roleForm.value.id, roleForm.value)
    if (res?.code === 200) {
        ElMessage.success('角色重命名成功')
        dialogRenameRole.value = false
        await loadRoles()
        await loadLines() // 刷新台词角色名
    } else {
        ElMessage.error(res?.message || '重命名失败')
    }
}

async function deleteRole(r) {
    const res = await roleAPI.deleteRole(r.id)
    if (res?.code === 200) {
        ElMessage.success('角色删除成功')
        await loadRoles()
        await loadLines() // 同步台词，角色应置空
    } else {
        ElMessage.error(res?.message || '删除失败')
    }
}

// —— 新建角色 —— //
const dialogCreateRole = ref(false)
const createRoleFormRef = ref(null)
const createRoleForm = ref({
    name: '',
    description: '',
    default_voice_id: null,
    project_id: projectId,
})

function openCreateRole() {
    createRoleForm.value = {
        name: '',
        description: '',
        default_voice_id: null,
        project_id: projectId,
    }
    dialogCreateRole.value = true
}

async function createRole() {
    // 简单防重名提示（前端软校验，最终以后端为准）
    const name = (createRoleForm.value.name || '').trim()
    if (!name) return ElMessage.warning('请输入角色名称')
    const dup = roles.value.some(r => r.name === name)
    if (dup) {
        // 允许创建同名与否以你后端为准，这里仅提醒
        await ElMessageBox.confirm(`已存在名为「${name}」的角色，仍要创建吗？`, '提示', {
            confirmButtonText: '继续创建',
            cancelButtonText: '取消',
            type: 'warning',
        }).catch(() => { return })
        if (!name) return // 用户取消
    }

    // 选择一种：roleAPI 或 request
    // 1) 如果你有 roleAPI.createRole：
    const res = await roleAPI.createRole(createRoleForm.value)

    // 2) 通用：直接用 request.post
    //   const res = await request.post('/roles', createRoleForm.value)

    if (res?.code === 200) {
        ElMessage.success('已创建角色')
        dialogCreateRole.value = false

        // 刷新角色与台词（有些页面需要马上用到）
        await loadRoles()
        await loadLines()

        // 如果选择了默认音色，同步映射，避免下拉延迟
        const newRole = (res.data) ? res.data : roles.value.find(r => r.name === name)
        if (newRole && createRoleForm.value.default_voice_id) {
            roleVoiceMap.value[newRole.id] = createRoleForm.value.default_voice_id
        }

        // 若你前面实现了“隐藏已删除同名角色”的本地黑名单，这里确保新建角色可见：
        if (typeof hiddenRoleNames !== 'undefined' && hiddenRoleNames?.value instanceof Set) {
            if (hiddenRoleNames.value.has(name)) {
                hiddenRoleNames.value.delete(name)
                try { localStorage.setItem(`hidden_roles_${projectId}`, JSON.stringify([...hiddenRoleNames.value])) } catch { }
            }
        }
    } else {
        ElMessage.error(res?.message || '创建失败')
    }
}
// 插入与删除
async function insertBelow(row) {
    if (!activeChapterId.value) return

    // 1) 先创建新行（后端返回 newId）
    const createRes = await lineAPI.createLine(projectId, {
        chapter_id: row.chapter_id,
        role_id: null,
        text_content: '',
        status: 'pending',
        line_order: 0 // 随便，后面统一重排
    })
    if (createRes?.code !== 200 || !createRes.data?.id) {
        return ElMessage.error(createRes?.message || '插入失败')
    }
    const newId = createRes.data.id
    // 2) 插入新行到当前行的下方（修改 lines 列表）
    const insertIndex = lines.value.findIndex(item => item.id === row.id)
    if (insertIndex === -1) {
        return ElMessage.error('找不到插入位置')
    }

    // 创建一个“空行”对象，插入到列表中
    const newLine = {
        ...row,
        id: newId,
        role_id: null,
        text_content: '',
        status: 'pending'
    }

    lines.value.splice(insertIndex + 1, 0, newLine)

    // 3) 重新构造 orderList，按当前顺序赋予新的 line_order
    const orderList = lines.value.map((line, index) => ({
        id: line.id,
        line_order: index + 1
    }))

    console.log('orderList', orderList)
    // 4) 调用批量重排接口
    const reorderRes = await lineAPI.reorderLinesByPut(orderList)

    if (reorderRes?.code === 200) {
        ElMessage.success('已插入并更新顺序')
        await loadLines()
    } else {
        ElMessage.error(reorderRes?.message || '更新顺序失败')
        await loadLines() // 以服务端为准
    }
}

async function deleteLine(row) {
    const delRes = await lineAPI.deleteLine(row.id)
    if (delRes?.code !== 200) {
        return ElMessage.error(delRes?.message || '删除失败')
    }
    await loadLines()

}

async function updateLineRole(row) {
    if (!row?.id || row.role_id === null) return
    console.log('updateLineRole', row)
    const res = await lineAPI.updateLine(row.id, {
        chapter_id: row.chapter_id,
        role_id: row.role_id,
    })

    if (res?.code === 200) {
        ElMessage.success('角色已更新')
    } else {
        ElMessage.error(res?.message || '角色更新失败')
    }
}


const textLocked = ref(false) // 防止多次触发

async function updateLineText(row) {
    if (!row?.id) return
    const res = await lineAPI.updateLine(row.id, {
        chapter_id: row.chapter_id,
        text_content: row.text_content,
    })

    if (res?.code === 200) {
        ElMessage.success('台词已更新')
    } else {
        ElMessage.error(res?.message || '更新失败')
    }
}


// —— 导出 Prompt / 导入第三方 JSON —— //
const dialogImportThird = ref(false)
const thirdJsonText = ref('')

function openImportThirdDialog() {
    thirdJsonText.value = ''
    dialogImportThird.value = true
}

// 读取本地 .json 文件，填充到文本框
async function readThirdJsonFile(file) {
    try {
        const text = await file.text()
        // 简单校验是否为数组
        const parsed = JSON.parse(text)
        if (!Array.isArray(parsed)) {
            ElMessage.error('JSON 须为数组')
            return false
        }
        thirdJsonText.value = JSON.stringify(parsed, null, 2)
        return false // 阻止 el-upload 的默认上传
    } catch (e) {
        ElMessage.error('读取文件失败或 JSON 非法')
        return false
    }
}

// 导出 Prompt：调用 GET /export-llm-prompt/{project_id}/{chapter_id}，下载 .txt 文件
async function exportLLMPrompt() {
    if (!projectId || !activeChapterId.value) return
    const res = await chapterAPI.exportLLMPrompt(projectId, activeChapterId.value)
    if (res?.code === 200) {
        const text = res.data || ''
        if (!text) {
            ElMessage.warning('返回内容为空')
            return
        }
        // 直接下载 .txt
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        const chapterName = currentChapter.value?.title || `chapter_${activeChapterId.value}`
        a.download = `prompt_${projectId}_${activeChapterId.value}_${chapterName}.txt`
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
        ElMessage.success('Prompt 已导出')
    } else {
        ElMessage.error(res?.message || '导出失败')
    }
}


// 导入第三方 JSON：先删除原台词，再导入
async function submitImportThird() {
    if (!projectId || !activeChapterId.value) return
    const raw = (thirdJsonText.value || '').trim()
    if (!raw) return ElMessage.warning('请先粘贴 JSON 内容')

    // 基础合法性校验
    let parsed
    try {
        parsed = JSON.parse(raw)
        if (!Array.isArray(parsed)) throw new Error()
    } catch {
        return ElMessage.error('JSON 非法：需要一个数组')
    }

    // 二次确认
    try {
        await ElMessageBox.confirm(
            '导入将会【删除本章节现有全部台词】并用第三方 JSON 重建，是否继续？',
            '确认导入',
            { type: 'warning', confirmButtonText: '继续', cancelButtonText: '取消' }
        )
    } catch {
        return // 用户取消
    }

    // 1) 先删除原有台词
    const delRes = await lineAPI.deleteLinesByChapter(activeChapterId.value)
    if (delRes?.code !== 200) {
        return ElMessage.error(delRes?.message || '删除原有台词失败')
    }
    ElMessage.success('已清空原有台词')

    // 2) 再导入第三方 JSON（multipart/form-data，字段名 data）
    const fd = new FormData()
    fd.append('data', JSON.stringify(parsed)) // 用规范化后的 JSON，避免多余空白

    const res = await chapterAPI.importThirdLines(projectId, activeChapterId.value, fd)
    if (res?.code === 200) {
        ElMessage.success('导入成功')
        dialogImportThird.value = false
        await loadLines()
        await loadRoles()
    } else {
        ElMessage.error(res?.message || '导入失败')
        // 可选：导入失败后要不要把之前删除的内容回滚？前端无法回滚，必要时后端做事务。
    }
}

// 完成配音，替换昵称

// 保证跟行顺序一一对应；若后端返回已按 line_order 排好，这段可省略
// const sortedLines = () => {
//   const list = [...lines.value]
//   // 如果有 line_order，就按它排；否则按当前顺序
//   list.sort((a, b) => {
//     const ao = a.line_order ?? Number.MAX_SAFE_INTEGER
//     const bo = b.line_order ?? Number.MAX_SAFE_INTEGER
//     return ao - bo
//   })
//   return list
// }

// 若你的后端返回的 lines 已经按 line_order 排好，可以直接用 lines.value

function getFolderFromPath(audioPath) {
    if (!audioPath) return ''
    const sep = audioPath.includes('\\') ? '\\' : '/'
    return audioPath.slice(0, audioPath.lastIndexOf(sep))
}
const replaceFilename = (p, name) => (p ? p.replace(/[^/\\]+$/, name) : name)
const addTempPrefix = (p) => (p ? p.replace(/([^/\\]+)$/, 'temp_$1') : null)

async function markAllAsCompleted() {
    const list = lines.value
    if (!list.length) {
        ElMessage.info('当前无台词')
        return
    }
    try {
        await ElMessageBox.confirm(
            '此操作将会批量导出所有台词音频，是否继续？',
            '提示',
            {
                confirmButtonText: '确认',
                cancelButtonText: '取消',
                type: 'warning',
            }
        )
    } catch {
        ElMessage.info('已取消操作')
        return
    }
    const loading = ElLoading.service({
        lock: true,
        text: '正在批量修改 audio_path（阶段 1/3）...',
        background: 'rgba(0,0,0,0.3)'
    })

    // —— 阶段 1：全部先加 temp_ 前缀 —— //
    let ok1 = 0, skip1 = 0, fail1 = 0
    for (const line of list) {
        if (!line.audio_path) { skip1++; continue }
        const base = /[^/\\]+$/.exec(line.audio_path)?.[0] || ''
        if (base.startsWith('temp_')) { skip1++; continue }

        const tmpPath = addTempPrefix(line.audio_path)
        if (!tmpPath) { skip1++; continue }

        try {
            const res = await lineAPI.updateLineAudioPath(line.id, {
                chapter_id: line.chapter_id,
                audio_path: tmpPath
            })
            const success = res?.code === 200 || res === true || res?.data === true
            if (success) {
                line.audio_path = tmpPath
                ok1++
            } else {
                fail1++
                console.error(`阶段1失败 line#${line.id}:`, res)
            }
        } catch (e) {
            fail1++
            console.error(`阶段1异常 line#${line.id}:`, e?.response?.data || e)
        }
    }

    // —— 阶段 2：按 line_order 重命名为 index{line_order}.wav —— //
    loading.setText('正在批量修改 audio_path（阶段 2/3）...')
    let ok2 = 0, skip2 = 0, fail2 = 0

    for (const line of list) {
        if (!line.audio_path) { skip2++; continue }

        const ord = Number.isInteger(line.line_order) ? line.line_order : null
        if (ord == null) { skip2++; continue }

        // 取台词前10字作为文件名一部分
        // 取台词前10字
        const text = (line.text_content || '').trim().slice(0, 10)

        // 去掉空格和中英文标点
        const cleanText = text.replace(/[\s\p{P}]/gu, '')

        // 再过滤掉文件名非法字符（Windows 不能包含 \/:*?"<>|）
        const safeText = cleanText.replace(/[\\/:*?"<>|]/g, '')

        const newName = `${ord}_${safeText}.wav`
        // const newName = `index${ord}.wav`
        const currentName = /[^/\\]+$/.exec(line.audio_path)?.[0]
        console.log('currentName=', currentName)
        if (currentName === newName) { skip2++; continue }

        const newPath = replaceFilename(line.audio_path, newName)
        try {
            const res = await lineAPI.updateLineAudioPath(line.id, {
                chapter_id: line.chapter_id,
                audio_path: newPath
            })
            const success = res?.code === 200 || res === true || res?.data === true
            if (success) {
                line.audio_path = newPath
                ok2++
            } else {
                fail2++
                console.error(`阶段2失败 line#${line.id}:`, res)
            }
        } catch (e) {
            fail2++
            console.error(`阶段2异常 line#${line.id}:`, e?.response?.data || e)
        }
    }

    // —— 阶段 3：导出音频与字幕（也显示在 Loading 里） —— //
    const total = list.length
    const msg1 = `阶段1：成功 ${ok1}，跳过 ${skip1}，失败 ${fail1}`
    const msg2 = `阶段2：成功 ${ok2}，跳过 ${skip2}，失败 ${fail2}`

    if (fail1 === 0 && fail2 === 0) {
        // 所有重命名成功，进入导出
        loading.setText('正在导出音频与字幕（阶段 3/3）...')

        try {
            // 如果你的后端一个接口同时导出音频和字幕
            const expRes = await lineAPI.exportLines(activeChapterId.value)

            // 如果你有单独的字幕导出接口，可按需增加：
            // const srtRes = (typeof lineAPI.exportSubtitles === 'function')
            //   ? await lineAPI.exportSubtitles(activeChapterId.value)
            //   : null

            const data = expRes?.data || {}
            // 尝试从返回体里拿关键信息（字段名以你后端为准）
            const audioOut = data.audio_zip_path || data.audio_zip || data.audio_path || data.audio
            const srtOut = data.subtitle_zip_path || data.srt_zip || data.subtitles_zip || data.srt

            // 在 Loading 里展示导出结果摘要
            loading.setText(
                `导出完成（阶段 3/3）：\n` +
                `- 音频：${audioOut ? audioOut : '已导出'}\n` +
                `- 字幕：${srtOut ? srtOut : '已导出'}\n` +
                `${msg1}；${msg2}`
            )

            // 友好提示
            ElMessage.success(`全部完成（共 ${total} 条）。${msg1}；${msg2}；导出成功`)
        } catch (e) {
            console.error('导出失败：', e)
            loading.setText(`导出失败（阶段 3/3）。${msg1}；${msg2}`)
            ElMessage.warning(`重命名成功，但导出失败。${msg1}；${msg2}`)
        } finally {
            loading.close()
        }
    } else {
        // 有失败就不做导出
        loading.close()
        ElMessage.warning(`部分失败。${msg1}；${msg2}（详见控制台）`)
    }

    // —— 自动打开输出文件夹 —— //
    // 若导出接口返回了目录，可优先打开导出目录；否则仍按原逻辑打开第一条音频所在目录
    try {
        const firstLineWithAudio = lines.value[0]
        const folderPath = firstLineWithAudio ? getFolderFromPath(firstLineWithAudio.audio_path) : ''
        if (native?.openFolder && folderPath) {
            native.openFolder(folderPath)
        }
    } catch { }
}



function playVoice(voiceId) {
    if (!voiceId) return
    const voice = voicesOptions.value.find(v => v.id === voiceId)
    if (!voice || !voice.reference_path) {
        ElMessage.warning('该音色未设置参考音频')
        return
    }

    try {
        const src = native?.pathToFileUrl ? native.pathToFileUrl(voice.reference_path) : voice.reference_path
        audioPlayer.pause()
        audioPlayer.src = src
        audioPlayer.currentTime = 0
        audioPlayer.play().catch(() => ElMessage.error('无法播放参考音频'))
    } catch {
        ElMessage.error('无法播放参考音频')
    }
}

// 音频处理
import WaveCellPro from '../components/WaveCellPro.vue'
import { fa } from 'element-plus/es/locales.mjs'
// 行音频版本号：lineId -> number
const audioVer = ref(new Map())

const getVer = (id) => audioVer.value.get(id) || 0
const bumpVer = (id) => audioVer.value.set(id, getVer(id) + 1)

// 生成给 WaveCellPro 用的 key（强制重建）与 src（带 ?v= 反缓存）
function waveKey(row) {
    return `${row.id}-${getVer(row.id)}`
}
function waveSrc(row) {
    if (!row.audio_path) return ''
    const base = native?.pathToFileUrl ? native.pathToFileUrl(row.audio_path) : row.audio_path
    const v = getVer(row.id)
    return v ? `${base}${base.includes('?') ? '&' : '?'}v=${v}` : base
}

// 全局单实例播放（同页只允许一条在播）
const waveHandleSet = new Set()
function registerWave(handle) {
    console.log('registerWave', handle)
    if (handle) waveHandleSet.add(handle)   // handle 需要有 pause()
}

function unregisterWave(handle) {     // 新增
    console.log('unregisterWave', handle)
    if (handle && waveHandleSet.has(handle)) {
        try { handle.pause && handle.pause() } catch { }
        waveHandleSet.delete(handle)
    }
}
function stopOthers(exceptHandle) {
    console.log('stopOthers', exceptHandle)
    waveHandleSet.forEach(h => {
        if (h && h !== exceptHandle) {
            try { h.pause && h.pause() } catch { }
        }
    })
}

// 确认后真正处理
async function confirmAndProcess(row, payload) {
    // payload: {speed, volume, start_ms, end_ms}
    const body = {
        speed: Number(payload.speed || row._procSpeed || 1.0),
        volume: Number(payload.volume || row._procVolume || 1.0),
        start_ms: payload.start_ms ?? null,
        end_ms: payload.end_ms ?? null,
    }
    console.log('confirmAndProcess', row.id, body)
    const res = await lineAPI.processAudio(row.id, body)
    if (res?.code === 200) {
        ElMessage.success('后端处理完成')
        // ✅ 关键：递增该行版本号 → WaveCellPro 的 :key 和 :src 都会变化 → 强制重载最新音频
        bumpVer(row.id)
        //await loadLines()                 // 刷新拿新路径
    } else {
        ElMessage.error(res?.message || '处理失败')
    }
}



// 枚举下拉
const emotionOptions = ref([])
const strengthOptions = ref([])

async function loadEnums() {
    const [emos, strengths] = await Promise.all([
        enumAPI.fetchAllEmotions(),
        enumAPI.fetchAllStrengths()
    ])
    emotionOptions.value = (emos || []).map(e => ({ value: e.id, label: e.name }))
    strengthOptions.value = (strengths || []).map(s => ({ value: s.id, label: s.name }))
}

// 更新情绪
async function updateLineEmotion(row) {
    if (!row?.id) return
    const res = await lineAPI.updateLine(row.id, {
        chapter_id: row.chapter_id,
        emotion_id: row.emotion_id,
    })
    if (res?.code === 200) {
        ElMessage.success('情绪已更新')
    } else {
        ElMessage.error(res?.message || '情绪更新失败')
    }
}

// 更新强度
async function updateLineStrength(row) {
    if (!row?.id) return
    const res = await lineAPI.updateLine(row.id, {
        chapter_id: row.chapter_id,
        strength_id: row.strength_id,
    })
    if (res?.code === 200) {
        ElMessage.success('强度已更新')
    } else {
        ElMessage.error(res?.message || '强度更新失败')
    }
}

onMounted(() => {
    loadEnums()
})
const dialogSelectVoice = ref({
    visible: false,
    role: null,  // 当前操作的角色
})

// 打开弹窗
function openVoiceDialog(role) {
    dialogSelectVoice.value.visible = true
    dialogSelectVoice.value.role = role
}

// 试听
function playVoice2(voiceId) {
    const voice = voicesOptions.value.find(v => v.id === voiceId)
    if (!voice?.reference_path) return ElMessage.warning('该音色无参考音频')
    try {
        const src = native?.pathToFileUrl ? native.pathToFileUrl(voice.reference_path) : voice.reference_path
        audioPlayer.pause()
        audioPlayer.src = src
        audioPlayer.currentTime = 0
        audioPlayer.play().catch(() => ElMessage.error('无法播放音频'))
    } catch {
        ElMessage.error('无法播放音频')
    }
}

// 确认绑定
async function confirmSelectVoice(voice) {
    const role = dialogSelectVoice.value.role
    if (!role) return
    roleVoiceMap.value[role.id] = voice.id

    // 更新到后端
    const payload = {
        name: role.name,
        project_id: role.project_id,
        default_voice_id: voice.id,
    }
    const res = await roleAPI.updateRole(role.id, payload)
    if (res?.code === 200) {
        ElMessage.success(`已为「${role.name}」绑定音色「${voice.name}」`)
        dialogSelectVoice.value.visible = false
    } else {
        ElMessage.error(res?.message || '绑定失败')
    }
}

</script>

<style scoped>
.page-wrap {
    display: flex;
    flex-direction: column;
    height: 100%;
    /* 承接父级高度（若父级未设，可换成 min-height:100vh） */
    min-height: 0;
    overflow: hidden;
}

.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

.title-side {
    display: flex;
    align-items: center;
    gap: 8px;
}

.proj-title {
    margin: 0 4px 0 8px;
    font-size: 20px;
    font-weight: 700;
}

.ml8 {
    margin-left: 8px;
}

.action-side {
    display: flex;
    align-items: center;
}

.main {
    border: 1px solid var(--el-border-color);
    border-radius: 12px;
    overflow: hidden;
}

.aside {
    border-right: 1px solid var(--el-border-color);
    padding: 12px;
    background: #fff;
}

.aside-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}

.aside-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 600;
}

.chapter-menu {
    border-right: none;
}

.chapter-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
}

.chapter-ops {
    display: flex;
    align-items: center;
    gap: 4px;
}

.ellipsis {
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.content {
    background: #fff;
    padding: 16px;
    /* overflow: hidden; */
}

.toolbar {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
}

.chapter-card {
    margin-bottom: 12px;
}

.chapter-card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.chapter-card-head .left {
    display: flex;
    align-items: center;
    gap: 8px;
}

.chapter-card-head .title {
    font-size: 16px;
    font-weight: 700;
}

.chapter-card-head .right {
    display: flex;
    align-items: center;
    gap: 8px;
}

.chapter-content-box {
    margin-top: 8px;
}

.chapter-scroll {
    max-height: 220px;
}

.chapter-text {
    white-space: pre-wrap;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    line-height: 1.6;
    color: #333;
    padding: 8px 2px;
}

.lines-table {
    border-radius: 10px;
    overflow: hidden;
}

.role-cell {
    display: flex;
    align-items: center;
}

.role-name {
    font-weight: 600;
    line-height: 1.2;
}

.role-voice {
    font-size: 12px;
    color: #666;
}

.role-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
}

.role-card {
    border-radius: 12px;
}

.role-card-head {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}

.role-meta {
    flex: 1;
    min-width: 0;
}

.role-title {
    font-weight: 700;
}

.role-desc {
    font-size: 13px;
    color: #666;
}

.ellipsis-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.bind-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    /* 左右分布 */
    margin-top: 8px;
}

.bind-left {
    display: flex;
    align-items: center;
    gap: 8px;
}

.bind-right {
    flex-shrink: 0;
    /* 防止按钮被压缩 */
}


.queue-item .queue-title {
    font-weight: 600;
}

.queue-item .queue-meta {
    font-size: 12px;
    color: #666;
}

.w220 {
    width: 220px;
}

.w260 {
    width: 260px;
}

.w300 {
    width: 300px;
}

.el-textarea__inner {
    font-size: 14px;
    line-height: 1.4;
    max-height: 120px;
    overflow-y: auto;
}

.voice-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 12px;
}

.voice-card {
    cursor: pointer;
    border-radius: 12px;
    transition: 0.2s;
}

.voice-card:hover {
    border-color: var(--el-color-primary);
}

.voice-card-head {
    margin-bottom: 8px;
}

.voice-title {
    font-weight: 600;
}

.voice-desc {
    font-size: 12px;
    color: #666;
}

.voice-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
</style>
