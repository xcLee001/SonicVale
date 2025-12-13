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
                <el-tag effect="light" type="danger" class="ml8">剩余生成：{{ queue_rest_size }}</el-tag>
                <!-- ✅ 精准填充状态 -->
                <el-tag class="ml8" effect="light" :type="project?.is_precise_fill == 1 ? 'success' : 'info'">
                    <el-icon style="margin-right: 4px;">
                        <CircleCheck v-if="project?.is_precise_fill == 1" />
                        <CircleClose v-else />
                    </el-icon>
                    精准填充：{{ project?.is_precise_fill == 1 ? '开启' : '关闭' }}
                </el-tag>

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
                    </el-icon> 消息队列
                </el-button>
            </div>
        </div>

        <el-container class="main">
            <!-- 左侧章节 -->
            <el-aside width="240px" class="aside">
                <div class="aside-head">
                    <div class="aside-title">
                        <div class="title-left">
                            <el-icon>
                                <Menu />
                            </el-icon>
                            <span>所有章节</span>
                        </div>

                        <el-button circle size="small" type="primary" plain @click="scrollToActiveChapter">
                            <el-icon>
                                <Refresh />
                            </el-icon>
                        </el-button>
                    </div>






                    <div class="aside-actions">


                        <el-button type="success" plain size="small" @click="handleBatchImport">
                            <el-icon>
                                <Upload />
                            </el-icon>
                            <span>批量导入</span>
                        </el-button>

                        <el-button type="primary" plain size="small" @click="dialogNewChapter = true">
                            <el-icon>
                                <Plus />
                            </el-icon>
                            <span>新建章节</span>
                        </el-button>
                    </div>
                    <el-input v-model="chapterKeyword" placeholder="搜索章节" clearable class="mb8">
                        <template #prefix><el-icon>
                                <Search />
                            </el-icon></template>
                    </el-input>
                </div>



                <!-- ✅ 替换开始 -->
                <!-- 让树撑满剩余高度 -->
                <div class="tree-container">
                    <el-tree-v2 ref="chapterTreeRef" :data="filteredChapters" :props="{ value: 'id', label: 'title' }"
                        :item-size=45 :height="treeHeight" :current-node-key="activeChapterId"
                        @node-click="onSelectChapter" :highlight-current="true" class="chapter-menu">
                        <template #default="{ data, node }">
                            <el-icon>
                                <Document />
                            </el-icon>
                            <div class="chapter-item" :class="{ 'is-active': activeChapterId === data.id }">
                                <div class="chapter-title ellipsis">{{ data.title }}</div>

                                <div class="chapter-ops">
                                    <el-button link @click.stop="openRenameChapter(data)" class="op-btn">
                                        <el-icon>
                                            <Edit />
                                        </el-icon>
                                    </el-button>

                                    <el-popconfirm title="确认删除该章节？" @confirm="deleteChapter(data)">
                                        <template #reference>
                                            <el-button link class="op-btn del-btn">
                                                <el-icon>
                                                    <Delete />
                                                </el-icon>
                                            </el-button>
                                        </template>
                                    </el-popconfirm>
                                </div>
                            </div>
                        </template>

                    </el-tree-v2>
                </div>


            </el-aside>

            <!-- 主区域 -->

            <el-main class="content">
                <!-- 未选择章节时显示提示 -->
                <div v-if="!activeChapterId" class="no-chapter-placeholder">
                    <el-empty description="请先在左侧选择一个章节" :image-size="160">
                        <template #image>
                            <el-icon :size="80" color="#c0c4cc">
                                <Document />
                            </el-icon>
                        </template>
                    </el-empty>
                </div>

                <!-- 已选择章节时显示内容 -->
                <template v-else>
                <!-- 章节正文 -->
                <el-card class="chapter-card">
                    <div class="chapter-card-head">
                        <div class="left">
                            <el-icon>
                                <Document />
                            </el-icon>
                            <span class="title">{{ currentChapter?.title || '未选择章节' }}</span>
                            <el-tag v-if="currentChapterContent" size="small" effect="light" class="ml8">
                                {{ currentChapterContent.length }} 字
                            </el-tag>
                            <el-tag v-if="currentChapterContent" size="small" effect="light" class="ml8">
                                {{ lines.length }} 行
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
                            <el-button @click="exportLLMPrompt" :disabled="!currentChapter">
                                <el-icon>
                                    <Document />
                                </el-icon> 导出 Prompt
                            </el-button>

                            <!-- 新增：导入第三方 JSON -->
                            <el-button @click="openImportThirdDialog" :disabled="!currentChapter">
                                <el-icon>
                                    <Upload />
                                </el-icon> 导入第三方 JSON
                            </el-button>
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

                <el-tabs v-model="activeTab" class="el-tabs-box">
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
                            <el-button type="warning" @click="batchAddTailSilence" class="ml8">
                                <el-icon>
                                    <Mute />
                                </el-icon>
                                批量添加间隔时间
                            </el-button>

                            <el-button type="success" @click="markAllAsCompleted">
                                <el-icon>
                                    <Check />
                                </el-icon> 导出配音与字幕
                            </el-button>
                            <el-button type="danger" @click="handleCorrectSubtitles">
                                <el-icon>
                                    <Edit />
                                </el-icon>
                                矫正字幕
                            </el-button>

                            <el-switch v-model="playMode" active-text="顺序播放" inactive-text="单条播放"
                                active-value="sequential" inactive-value="single" />


                        </div>

                        <!-- ✅ 新版：虚拟滚动表格 -->
                        <div class="table-box">
                            <el-auto-resizer v-slot="{ height, width }">
                                <el-table-v2 :data="displayedLines" :columns="lineColumns" :row-height="200" fixed
                                    :width="width" :height="height" row-key="id" class="lines-table" />
                            </el-auto-resizer>
                        </div>
                    </el-tab-pane>

                    <!-- 角色库 -->
                    <el-tab-pane label="角色库" name="roles">

                        <div class="toolbar">
                            <el-input v-model="roleKeyword" placeholder="搜索角色" clearable class="w260" />
                            <el-button @click="loadRoles" class="ml8">
                                <el-icon>
                                    <Refresh />
                                </el-icon> 刷新
                            </el-button>
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
                            <el-tooltip placement="top" content="此功能为测试版，结果可能不稳定，并且效果依赖于音色的标签，因此尽可能完善丰富音色标签。">
                                <el-button type="danger" @click="addSmartRoleAndVoice">
                                    <el-icon>
                                        <MagicStick />
                                    </el-icon>
                                    智能匹配音色（Beta）
                                </el-button>
                            </el-tooltip>


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

                                        <el-button circle plain :disabled="!roleVoiceMap[r.id]"
                                            @click="toggleVoicePlay(roleVoiceMap[r.id])"
                                            :title="isPlaying && currentVoiceId === roleVoiceMap[r.id] ? '暂停' : '试听音色'">
                                            <el-icon>
                                                <Headset />
                                            </el-icon>
                                        </el-button>

                                    </div>

                                    <!-- 右边：选择音色 -->
                                    <div class="bind-right">
                                        <el-button :type="getRoleVoiceName(r.id) ? 'primary' : 'danger'" size="small"
                                            @click="openVoiceDialog(r)">
                                            {{ getRoleVoiceName(r.id) ? '更换音色' : '绑定音色' }}
                                        </el-button>

                                    </div>
                                </div>


                            </el-card>
                        </div>


                    </el-tab-pane>
                </el-tabs>
                </template>
            </el-main>

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
                    <div v-if="!settingsForm.llm_model && settingsForm.llm_provider_id"
                        style="color: #f56c6c; font-size: 12px; margin-top: 4px;">
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
                        <el-option v-for="p in prompts" :key="p.id" :label="p.name" :value="p.id" />
                    </el-select>
                </el-form-item>
                <!-- ✅ 精准填充开关（0/1） -->
                <!-- ✅ 精准填充开关 + 小问号解释 -->
                <el-form-item>
                    <template #label>
                        <span class="label-with-help">
                            精准填充
                            <el-tooltip effect="dark" placement="top" content="开启后，会自动填充LLM拆分后遗漏的句子或者词语">
                                <el-icon class="help-icon">
                                    <QuestionFilled />
                                </el-icon>
                            </el-tooltip>
                        </span>
                    </template>

                    <el-switch v-model="settingsForm.is_precise_fill" :active-value="1" :inactive-value="0"
                        active-text="开启" inactive-text="关闭" />
                </el-form-item>
                <el-form-item label="项目根路径" prop="project_root_path">
                    <el-input v-model="settingsForm.project_root_path" readonly
                        placeholder="例如：D:\\Works\\MyProject 或 /Users/me/Projects/demo" >
                        <template #append>
                            <el-button @click="openRootDir">打开目录</el-button>
                        </template>
                        </el-input>
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
                title="请粘贴一个 JSON 数组，每个元素形如 { role_name: string, text_content: string, emotion_name: string, strength_name: string}；提交后将直接写入该章节台词。" />
            <el-input v-model="thirdJsonText" type="textarea" :rows="14"
                placeholder='[{"role_name":"旁白","text_content":"……","emotion_name": "平静", "strength_name": "中等"}]' />
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

        <el-dialog v-model="dialogSelectVoice.visible" title="选择音色" width="780px">
            <!-- 筛选区 -->
            <div class="filter-bar">
                <el-select ref="filterSelectRef" v-model="filterTags" multiple filterable clearable collapse-tags
                    collapse-tags-tooltip placeholder="按标签筛选" class="filter-select" @change="handleTagChange">
                    <el-option v-for="tag in allTags" :key="tag" :label="tag" :value="tag" />
                </el-select>

                <!-- 新增名字搜索框 -->
                <el-input v-model="searchName" placeholder="搜索名字" clearable style="margin-left: 8px; width: 200px;" />
            </div>


            <!-- 音色卡片网格 -->
            <div class="voice-grid">
                <el-card v-for="v in filteredVoices" :key="v.id" class="voice-card" shadow="hover"
                    @click="selectVoice(v)">
                    <div class="voice-card-head">
                        <div class="voice-title">{{ v.name }}</div>
                        <div class="voice-desc">
                            <el-tag v-for="(tag, index) in (v.description ? v.description.split(',') : [])" :key="index"
                                type="info" effect="plain" size="small">
                                {{ tag }}
                            </el-tag>
                            <span v-if="!v.description">无标签</span>
                        </div>
                    </div>

                    <div class="voice-actions">
                        <el-button circle @click.stop="toggleVoicePlay(v.id)"
                            :title="isPlaying && currentVoiceId === v.id ? '暂停' : '试听'">
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
import {
    Lock, Unlock, ArrowLeft, Setting, Headset, Menu, Plus, Search, Edit, Delete, Refresh, MagicStick, Document, CaretBottom, CaretRight, Upload, VideoPlay, VideoPause, Mute, Check,
    CircleCheck, CircleClose, QuestionFilled
} from '@element-plus/icons-vue'
import service from '../api/config'
import * as chapterAPI from '../api/chapter'
import * as roleAPI from '../api/role'
import * as projectAPI from '../api/project'
import * as lineAPI from '../api/line'
import * as voiceAPI from '../api/voice'
import * as providerAPI from '../api/provider'
import * as enumAPI from '../api/enums' // 例如 emotion/strength API
import * as promptAPI from '../api/prompt'
import { ElTableV2 } from 'element-plus'
import { h } from 'vue'
import {
    ElInput,
    ElSelect,
    ElOption,
    ElTag,
    ElText,
    ElButton,
    ElPopconfirm,
    ElSwitch
} from 'element-plus'
const emotionLocked = ref(false)
const strengthLocked = ref(false)

const roleColumnLocked = ref(false)
// //////////////////////////////////websocket
// ---- WebSocket（局部，纯 JS）+ 任务队列 ----
import { onUnmounted } from 'vue'
const queue_rest_size = ref(0) // 后端返回的队列剩余长度


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
    const { line_id, status } = msg
    const idx = lines.value.findIndex(l => l.id === line_id)
    if (idx >= 0) {
        const old = lines.value[idx]
        lines.value[idx] = {
            ...old,
            status,                                  // 'pending' | 'processing' | 'done' | 'failed'
        }
        // ✅ 关键：当生成完成时，强制重载对应 WaveCellPro
        if (status === 'done') {
            console.log("音频生成完成，强制重载对应 WaveCellPro")
            bumpVer(line_id)           // 让 :key 与 :src?v= 都变

        }

    } else {
        // 当前章节列表里没有该行（例如切换了章节），这里先忽略。
        // 需要的话也可以触发一次局部刷新：activeChapterId.value && loadLines()
    }
}

const HEARTBEAT_INTERVAL = 150000;   // 60s 发送一次 ping，正常来说一般15s
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
                // 同时弹出提示框
                // console.log(`[${new Date().toLocaleTimeString()}] #${msg.line_id} ${meta}`)
                addQueue({ title: `台词 #${msg.line_id}`, meta, type })
                applyLineUpdate(msg)
                queue_rest_size.value = msg.progress
                if (msg.progress === 0 && msg.status !== 'processing') {
                    // 播放简短提示音
                    const audio = new Audio(new URL('../assets/完成提示音.mp3', import.meta.url).href)
                    audio.volume = 0.3  // ← 调低音量到 30%，你可以调到 0.1~0.5 之间
                    audio.play().catch(err => {
                        console.warn('播放完成提示音失败：', err)
                    })
                    // 可配合消息提示
                    // ElMessage({
                    //     message: '🎵 所有音频已生成完成！',
                    //     type: 'success'
                    // })
                    addQueue({ title: '🎉 所有音频已生成完成！', type: 'success' })
                }

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
    prompt_id: null,
    is_precise_fill: null,      // ✅ 新增字段，默认 0
    project_root_path: null,
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
        prompt_id: project.value?.promptId ?? project.value?.prompt_id ?? null,
        is_precise_fill: project.value?.is_precise_fill ?? null,
        project_root_path: project.value?.project_root_path ?? null

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

async function openRootDir  (){
    await native.openFolder(settingsForm.value.project_root_path)
}
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
            prompt_id: settingsForm.value.prompt_id,
            is_precise_fill: settingsForm.value.is_precise_fill,
            project_root_path: settingsForm.value.project_root_path
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
    // 不再自动选择章节，由 restoreLastChapter 处理
    if (activeChapterId.value && chapters.value.find(c => c.id === activeChapterId.value)) {
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

function loadChapterContent(indexStr) {
    activeChapterId.value = Number(indexStr)
    loadLines()
    loadChapterDetail(activeChapterId.value)
}
// ✅ 修改后（TreeV2 版本）
const onSelectChapter = (data) => {
    // data 是章节对象，例如 { id: 1, title: "第一章 起始" }
    activeChapterId.value = data.id

    // 如果你原本有加载章节内容的逻辑：
    loadChapterContent?.(data.id)
    // 记忆
    saveLastChapter();
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
        // 
        // ③ 状态筛选 ✅ 新增
        .filter(l => (!statusFilter.value ? true : l.status === statusFilter.value))
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

    try {
        if (row.is_done !== 0) {
            row.is_done = 0
            updateLineIsDone(row, 0)
        }
        // ✅ 用户点击“确定”后才继续执行以下逻辑
        addQueue({ title: `台词 #${row.id}`, meta: '已入队，开始生成', type: 'info' })

        const body = {
            chapter_id: row.chapter_id,
            role_id: row.role_id,
            voice_id: getRoleVoiceId(row.role_id),
            id: row.id,
            emotion_id: row.emotion_id,
            strength_id: row.strength_id,
            text_content: row.text_content,
            audio_path: row.audio_path,
        }

        console.log('准备生成音频:', body)

        const res = await lineAPI.generateAudio(projectId, activeChapterId.value, body)

        if (res?.code === 200) {

            ElMessage.success('已添加到异步任务中')
            // 前端转换状态，会不会影响？有待商定是自己动变更，还是等后端推送
            row.status = 'processing'
            // 强制刷新行
            // await loadLines()

        } else {
            addQueue({
                title: `台词 #${row.id}`,
                meta: res?.message || '生成失败（请求失败）',
                type: 'danger',
            })
            ElMessage.error(res?.message || '生成失败')
        }
    } catch (err) {
        // ✅ 用户点击“取消”或关闭弹窗时
        if (err === 'cancel' || err === 'close') {
            ElMessage.info('已取消生成操作')
        } else {
            console.error('生成出错:', err)
            ElMessage.error('生成失败，请稍后再试')
        }
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
    return roles.value.filter(r => r.name.toLowerCase().includes(kw)).sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
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
    restoreLastChapter() // 恢复上次章节
    scrollToActiveChapter() // 定位到选中的章节
    await loadLines()
    await loadChapterDetail(activeChapterId.value)
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
async function addSmartRoleAndVoice() {
    // 二次确认
    try {
        await ElMessageBox.confirm(`确定要智能进行匹配音色吗？`, '提示', {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning',
        })
    } catch {
        return // 用户取消
    }
    const loading = ElLoading.service({
        lock: true,
        text: '正在智能匹配角色和音色，请稍候...',
        background: 'rgba(0, 0, 0, 0.4)',
    })
    // 发送请求（必须 await + 声明 res）
    try {
        const res = await chapterAPI.addSmartRoleAndVoice(projectId, activeChapterId.value)
        if (res?.code === 200) {
            // 提取出res.data列表中所有角色名
            const names = res.data.map(r => r.role_name)

            ElMessage.success(`已为「${names}」智能匹配音色`)
            await loadRoles()
            await loadLines()  // 同步台词角色名
        } else {
            ElMessage.error(res?.message || '匹配音色失败')
        }
    } catch (e) {
        ElMessage.error('匹配音色异常')
    } finally {
        loading.close()
    }

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
        role_id: row.role_id,
        text_content: '',
        status: 'pending',
        line_order: 0, // 随便，后面统一重排
        is_done: 0,
        emotion_id: row.emotion_id,
        strength_id: row.strength_id
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
        status: 'pending',
        is_done: 0,
        // 情绪和强度继承当前行

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
// 插入到顶部
async function insertAtTop() {
    if (!activeChapterId.value) return

    // 1) 先创建新行（后端返回 newId）
    const createRes = await lineAPI.createLine(projectId, {
        chapter_id: activeChapterId.value,
        role_id: null,
        text_content: '',
        status: 'pending',
        line_order: 0 // 随便，后面统一重排
    })
    if (createRes?.code !== 200 || !createRes.data?.id) {
        return ElMessage.error(createRes?.message || '插入失败')
    }
    const newId = createRes.data.id

    // 2) 创建“空行”对象，插到最前面
    const newLine = {
        id: newId,
        chapter_id: activeChapterId.value,
        role_id: null,
        text_content: '',
        status: 'pending'
    }

    lines.value.unshift(newLine) // 插到数组开头

    // 3) 重新构造 orderList
    const orderList = lines.value.map((line, index) => ({
        id: line.id,
        line_order: index + 1
    }))

    // 4) 调用批量重排接口
    const reorderRes = await lineAPI.reorderLinesByPut(orderList)

    if (reorderRes?.code === 200) {
        ElMessage.success('已在第一行插入并更新顺序')
        await loadLines()
    } else {
        ElMessage.error(reorderRes?.message || '更新顺序失败')
        await loadLines()
    }
}


async function deleteLine(row) {
    // 1) 调用后端删除
    const delRes = await lineAPI.deleteLine(row.id)
    if (delRes?.code !== 200) {
        return ElMessage.error(delRes?.message || '删除失败')
    }

    // 2) 前端移除这一行
    const deleteIndex = lines.value.findIndex(item => item.id === row.id)
    if (deleteIndex !== -1) {
        lines.value.splice(deleteIndex, 1)
    }

    // 3) 重排顺序
    const orderList = lines.value.map((line, index) => ({
        id: line.id,
        line_order: index + 1
    }))

    const reorderRes = await lineAPI.reorderLinesByPut(orderList)

    if (reorderRes?.code === 200) {
        ElMessage.success('已删除并更新顺序')
        await loadLines()
    } else {
        ElMessage.error(reorderRes?.message || '更新顺序失败')
        await loadLines() // 以服务端为准
    }
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
        // 
    } else {
        ElMessage.error(res?.message || '角色更新失败')
    }
}


const textLocked = ref(false) // 防止多次触发

async function updateLineText(row) {
    if (!row?.id) return

    // ✅ 如果没改动就不发请求
    if (row.tempText === undefined || row.tempText === row.text_content) return

    const oldText = row.text_content
    row.text_content = row.tempText // 提交临时值

    try {
        const res = await lineAPI.updateLine(row.id, {
            chapter_id: row.chapter_id,
            text_content: row.text_content,
        })

        if (res?.code === 200) {
            ElMessage.success('台词已更新')
            delete row.tempText // 清空临时缓存

            // ✅ 文本更新后自动重置状态
            if (row.is_done !== 0) {

                await updateLineIsDone(row, 0)
                row.is_done = 0
            }
        } else {
            // ❌ 失败回滚
            row.text_content = oldText
            ElMessage.error(res?.message || '更新失败')
        }
    } catch (err) {
        // ❌ 网络或异常情况回滚
        row.text_content = oldText
        ElMessage.error('请求出错')
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

        const action = await ElMessageBox.confirm(
            '是否复制到剪贴板？（取消则下载文件）',
            '导出方式',
            {
                confirmButtonText: '复制',
                cancelButtonText: '下载',
                type: 'info',
                distinguishCancelAndClose: true
            }
        ).catch(() => 'download') // 如果关闭或取消，就走下载

        if (action === 'confirm') {
            await navigator.clipboard.writeText(text)
            ElMessage.success('已复制到剪贴板')
        } else {
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
        }
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
            let isExportSingleSubtitle = false
            try {
                await ElMessageBox.confirm(
                    '是否额外导出所有的单条字幕？<br><span style="color:#999;">（额外导出会增加音频导出时间，推荐选择“否”）</span>',
                    '导出设置',
                    {
                        dangerouslyUseHTMLString: true, // 允许用 HTML 格式
                        confirmButtonText: '是',
                        cancelButtonText: '否',
                        type: 'info',
                        cancelButtonClass: 'el-button--danger'    // 「否」= 蓝色重点按钮
                    }
                )
                // 用户点击了“是”
                isExportSingleSubtitle = true
            } catch {
                // 用户点击了“否” 或者关闭
                isExportSingleSubtitle = false
            }
            const expRes = await lineAPI.exportLines(activeChapterId.value, isExportSingleSubtitle)

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
// 从 Set 换成 Map
const waveHandleMap = new Map()

function registerWave({ handle, id }) {
    if (handle && id) {
        console.log('registerWave', id, handle)
        waveHandleMap.set(id, handle)   // 直接覆盖
    }
}

function unregisterWave({ handle, id }) {
    console.log('unregisterWave', id)
    if (id && waveHandleMap.has(id)) {
        try { waveHandleMap.get(id)?.pause?.() } catch { }
        waveHandleMap.delete(id)
    }
}

function stopOthers(exceptHandle) {
    waveHandleMap.forEach((h, id) => {
        if (h && h !== exceptHandle) {
            try { h.pause?.() } catch { }
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
        silence_sec: Number(payload.silence_sec || 0),
        current_ms: payload.current_ms ?? null
    }
    // 添加校验逻辑，裁剪和指定位置添加静音不能同时进行
    // 1️⃣ 裁剪区间和“指定位置插入静音”不能同时存在
    const hasCut = body.start_ms !== null && body.end_ms !== null && body.end_ms > body.start_ms
    const hasInsertSilence = body.current_ms !== null && body.silence_sec !== 0

    if (hasCut && hasInsertSilence) {
        ElMessage.warning('❌ 裁剪区间与指定位置添加静音不能同时使用')
        return
    }
    console.log('confirmAndProcess', row.id, body)
    const res = await lineAPI.processAudio(row.id, body)
    if (res?.code === 200) {
        ElMessage.success('后端处理完成')
        // ✅ 关键：递增该行版本号 → WaveCellPro 的 :key 和 :src 都会变化 → 强制重载最新音频
        bumpVer(row.id)
        //await loadLines()                 // 刷新拿新路径
        // ✅ 重置完成状态
        if (row.is_done !== 0) {
            row.is_done = 0
            // console.log(`台词 #${row.id} 音频处理后，状态重置为未完成`)
            await updateLineIsDone(row, 0)
        }

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
const filterTags = ref([])

// 所有标签集合（从 voicesOptions 提取）
const allTags = computed(() => {
    const set = new Set()
    voicesOptions.value.forEach(v => {
        (v.description ? v.description.split(',') : []).forEach(tag => {
            if (tag.trim()) set.add(tag.trim())
        })
    })
    return Array.from(set)
})

// 按标签筛选
const searchName = ref('') // 新增

const filteredVoices = computed(() => {
    return voicesOptions.value.filter(v => {
        // 先处理名字匹配
        const matchName = !searchName.value || v.name.includes(searchName.value)

        // 再处理标签匹配
        if (!filterTags.value.length) return matchName
        const tags = v.description ? v.description.split(',') : []
        const matchTags = filterTags.value.every(ft => tags.includes(ft))

        return matchName && matchTags
    })
})

const filterSelectRef = ref(null)

function handleTagChange() {
    // 等下一个 tick 再关闭，不然选中状态可能丢失
    setTimeout(() => {
        filterSelectRef.value.blur()
    }, 0)
}
function cellStyle({ row, column }) {
    // 角色列无数据
    if (column.property === 'role_id' && !row.role_id) {
        return { backgroundColor: '#ffecec', color: '#d93025' }
    }

    // 台词文本列无数据
    if (column.label === '台词文本' && (!row.text_content || !row.text_content.trim())) {
        return { backgroundColor: '#ffecec', color: '#d93025' }
    }

    // 情绪列无数据
    if (column.label === '情绪' && !row.emotion_id) {
        return { backgroundColor: '#ffecec', color: '#d93025' }
    }

    // 强度列无数据
    if (column.label === '强度' && !row.strength_id) {
        return { backgroundColor: '#ffecec', color: '#d93025' }
    }

    return {}
}
async function handleCorrectSubtitles() {
    // 打开等待窗口
    const loading = ElLoading.service({
        lock: true,
        text: '正在矫正字幕，请稍候...',
        background: 'rgba(0, 0, 0, 0.5)'
    })

    try {
        const res = await lineAPI.correctLines(activeChapterId.value)
        if (res?.code !== 200) {
            ElMessage.error(res?.message || '请先导出音频与字幕')
        }
        else {
            ElMessage.success('字幕已矫正完成')
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
        // TODO: 刷新数据
    } catch (err) {
        console.error('字幕矫正错误详情：', err)
        ElMessage.error(`字幕矫正失败：${err.message || err}`)
    } finally {
        // 关闭等待窗口
        loading.close()
    }
}

async function batchAddTailSilence() {
    if (!lines.value.length) {
        return ElMessage.info('当前无台词');
    }

    try {
        const { value } = await ElMessageBox.prompt(
            '请输入末尾静音时长（秒）(建议不要超过0.6秒)（可为负数，负数表示裁剪）',
            '批量处理间隔时间',
            {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                // 支持整数、小数、负数
                inputPattern: /^-?\d+(\.\d+)?$/,
                inputErrorMessage: '请输入合法数字（可为负数）',
            }
        );
        const tailSec = Number(value);

        const loading = ElLoading.service({
            lock: true,
            text: '正在批量处理音频...',
            background: 'rgba(0,0,0,0.3)',
        });

        let ok = 0, fail = 0, skip = 0;

        for (const row of lines.value) {
            if (!row.audio_path) {
                skip++;
                continue;
            }
            try {
                const res = await lineAPI.processAudio(row.id, {
                    speed: row._procSpeed || 1.0,
                    volume: row._procVolume || 1.0,
                    start_ms: null,
                    end_ms: null,
                    silence_sec: tailSec, // 可正可负
                    current_ms: null
                });
                if (res?.code === 200) {
                    bumpVer(row.id); // 强制刷新 WaveCellPro
                    ok++;
                } else {
                    fail++;
                }
            } catch {
                fail++;
            }
        }

        loading.close();
        ElMessage.success(`批量完成：成功 ${ok} 条，跳过 ${skip} 条，失败 ${fail} 条`);
    } catch {
        // 用户取消输入
    }
}
// const playMode = ref('sequential') // 'single' = 单条, 'sequential' = 顺序
const playMode = ref(localStorage.getItem('playMode') || 'sequential')

// 监听 playMode 变化并存储到本地
watch(playMode, (val) => {
    localStorage.setItem('playMode', val)
})
// 处理 ended 事件
function handleEnded({ handle, id }) {
    console.log('handleEnded', id, playMode.value)
    if (playMode.value !== 'sequential') return

    // 拿到当前行列表（确保按 line_order 排序）
    const list = [...displayedLines.value].sort((a, b) => a.line_order - b.line_order)
    const idx = list.findIndex(l => l.id === id)
    console.log('当前行索引', idx, '，总行数', list.length)
    if (idx === -1 || idx === list.length - 1) return // 找不到或最后一条

    if (idx === -1) {
        console.warn('handleEnded: 未找到当前行，终止顺序播放')
        return
    }
    if (idx === list.length - 1) {
        console.log('handleEnded: 已是最后一行，顺序播放结束')
        return
    }

    // 向后查找下一个有音频的行
    let nextRow = null
    for (let i = idx + 1; i < list.length; i++) {
        if (list[i].audio_path) {
            nextRow = list[i]
            break
        }
    }

    if (!nextRow) {
        console.log('handleEnded: 后续没有可播放的音频，顺序播放结束')
        return
    }

    // 找到下一行对应的 WaveCellPro 实例
    console.log('下一行 ID:', nextRow.id)


    const nextHandle = waveHandleMap.get(nextRow.id)

    if (!nextHandle) {
        console.warn('handleEnded: 未找到下一行的 WaveCellPro 实例，行ID:', nextRow.id)
        return
    }

    if (nextHandle?.play) {
        console.log('handleEnded: 播放下一行 => ID:', nextRow.id)
        stopOthers(nextHandle) // 停止其他行
        nextHandle.play()
    } else {
        console.warn('handleEnded: 下一行实例没有 play 方法 => ID:', nextRow.id)
    }
}
// =============== ElTableV2 列配置 ===============
// ✅ 通用高亮包装函数（放在 <script setup> 顶部或表格定义前）
const statusFilter = ref('')
const wrapCellHighlight = (condition, children) => {
    return h(
        'div',
        {
            style: {
                width: '100%',
                height: '100%',
                backgroundColor: condition ? '#fde2e2' : 'transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                gap: '4px',
                boxSizing: 'border-box',
                padding: '4px',
                borderRadius: '4px',
                transition: 'background-color 0.3s ease',
            },
        },
        children
    )
}
import { reactive } from 'vue'
const lineColumns = reactive([
    {
        key: 'line_order',
        title: '序',
        width: 60,
        minWidth: 40,
        maxWidth: 60,
        align: 'center',
        cellRenderer: ({ rowData }) => rowData.line_order,
    },
    {
        key: 'role_id',
        title: '角色',
        width: 100,
        minWidth: 50,
        maxWidth: 150,
        align: 'center',
        cellRenderer: ({ rowData }) =>
            wrapCellHighlight(!rowData.role_id, [
                h(
                    ElSelect,
                    {
                        modelValue: rowData.role_id,
                        filterable: true,
                        clearable: true,
                        size: 'small',
                        disabled: roleColumnLocked.value,
                        placeholder: '选择角色',
                        style: { width: '100%' },
                        onChange: (val) => {
                            rowData.role_id = val
                            updateLineRole(rowData)
                            // 角色切换后，变更状态为未完成
                            // 2️⃣ 切换角色后自动置为未完成
                            if (rowData.is_done !== 0) {

                                // 3️⃣ 同步更新后端状态
                                updateLineIsDone(rowData, 0)
                                rowData.is_done = 0
                            }
                        },
                    },
                    () => roles.value.map((r) =>
                        h(ElOption, { label: r.name, value: r.id })
                    )
                ),
                h(
                    ElTag,
                    {
                        size: 'small',
                        type: getRoleVoiceName(rowData.role_id)
                            ? 'success'
                            : 'info',
                    },
                    () => getRoleVoiceName(rowData.role_id) || '未绑定音色'
                ),
            ]),
    },
    {
        key: 'text_content',
        title: '台词文本',
        width: 250,
        minWidth: 100,
        maxWidth: 300,
        align: 'center',
        cellRenderer: ({ rowData }) =>
            wrapCellHighlight(
                !(rowData.tempText?.trim() || rowData.text_content?.trim()),
                [
                    h(ElInput, {
                        modelValue: rowData.tempText ?? rowData.text_content,
                        'onUpdate:modelValue': (val) => (rowData.tempText = val),
                        size: 'small',
                        type: 'textarea',
                        autosize: { minRows: 2, maxRows: 9 }, // ✅ 只用 autosize 控高
                        placeholder: '输入台词内容',
                        disabled: textLocked.value,

                        onBlur: () => updateLineText(rowData),

                    }),
                ]
            ),
    }
    ,
    {
        key: 'emotion_id',
        title: '情绪',
        width: 120,
        minWidth: 80,
        maxWidth: 150,
        align: 'center',
        cellRenderer: ({ rowData }) =>
            wrapCellHighlight(!rowData.emotion_id, [
                h(
                    ElSelect,
                    {
                        modelValue: rowData.emotion_id,
                        size: 'small',
                        placeholder: '选择情绪',
                        disabled: emotionLocked.value,
                        clearable: true,
                        style: { width: '100%' },
                        onChange: (val) => {
                            rowData.emotion_id = val
                            updateLineEmotion(rowData)
                            if (rowData.is_done !== 0) {

                                // 3️⃣ 同步更新后端状态
                                updateLineIsDone(rowData, 0)
                                rowData.is_done = 0
                            }
                        },
                    },
                    () =>
                        emotionOptions.value.map((e) =>
                            h(ElOption, { label: e.label, value: e.value })
                        )
                ),
            ]),
    },
    {
        key: 'strength_id',
        title: '强度',
        width: 120,
        minWidth: 80,
        maxWidth: 150,
        align: 'center',
        cellRenderer: ({ rowData }) =>
            wrapCellHighlight(!rowData.strength_id, [
                h(
                    ElSelect,
                    {
                        modelValue: rowData.strength_id,
                        size: 'small',
                        placeholder: '选择强度',
                        disabled: strengthLocked.value,
                        clearable: true,
                        style: { width: '100%' },
                        onChange: (val) => {
                            rowData.strength_id = val
                            updateLineStrength(rowData)
                            if (rowData.is_done !== 0) {
                                rowData.is_done = 0
                                // 3️⃣ 同步更新后端状态
                                updateLineIsDone(rowData, 0)
                            }
                        },
                    },
                    () =>
                        strengthOptions.value.map((s) =>
                            h(ElOption, { label: s.label, value: s.value })
                        )
                ),
            ]),
    },
    {
        key: 'audio',
        title: '试听 / 处理',
        align: 'center',
        width: 500,
        minWidth: 300,
        maxWidth: 500,
        cellRenderer: ({ rowData }) =>
            h('div', {
                style: {
                    width: '100%',
                    height: '100%',           // ✅ 填满整行
                    display: 'flex',          // ✅ 居中显示
                    alignItems: 'center',
                    justifyContent: 'center',
                },
            }, [
                rowData.audio_path
                    ? h(WaveCellPro, {
                        key: waveKey(rowData),
                        src: waveSrc(rowData),
                        speed: rowData._procSpeed || 1.0,
                        volume2x: rowData._procVolume ?? 1.0,
                        'start-ms': rowData.start_ms,
                        'end-ms': rowData.end_ms,
                        style: {

                            maxHeight: '100%',   // ✅ 防止溢出
                            objectFit: 'contain',
                        },
                        onReady: (p) => registerWave({ handle: p, id: rowData.id }),
                        onRequestStopOthers: stopOthers,
                        onDispose: unregisterWave,
                        onConfirm: (p) => confirmAndProcess(rowData, p),
                        onEnded: (p) => handleEnded({ p, id: rowData.id }),
                    })
                    : h(ElText, { type: 'info' }, () => '无音频'),
            ]),
    },

    {
        key: 'edit',
        title: '操作',
        width: 150,
        minWidth: 100,
        maxWidth: 200,
        align: 'center',
        headerCellRenderer: () =>
            h(
                ElButton,
                { size: 'small', type: 'success', plain: true, onClick: insertAtTop },
                () => '首行插入'
            ),
        cellRenderer: ({ rowData }) =>
            h('div', { style: 'display:flex;justify-content:center;gap:4px;' }, [
                h(
                    ElButton,
                    {
                        size: 'small',
                        type: 'primary',
                        plain: true,
                        onClick: () => insertBelow(rowData),
                    },
                    () => '插入'
                ),
                h(
                    ElPopconfirm,
                    {
                        title: '确认删除该台词？',
                        onConfirm: () => deleteLine(rowData),
                    },
                    {
                        reference: () =>
                            h(
                                ElButton,
                                { size: 'small', type: 'danger', plain: true },
                                () => '删除'
                            ),
                    }
                ),
            ]),
    },
    {
        key: 'status',
        title: '状态',
        width: 100,
        minWidth: 100,
        maxWidth: 150,
        align: 'center',
        fixed: 'right',
        // ✅ 自定义表头，包含“状态”文字 + 下拉框
        headerCellRenderer: () =>
            h(
                'div',
                { class: 'status-header' },
                [
                    // 左侧文字标签
                    h('span', { class: 'status-title' }, '状态'),

                    // 状态筛选下拉框
                    h(
                        ElSelect,
                        {
                            modelValue: statusFilter.value,
                            placeholder: '全部',
                            clearable: true,
                            size: 'small',
                            class: 'status-select',
                            onChange: (val) => (statusFilter.value = val),
                        },
                        () => [
                            h(ElOption, { label: '全部', value: '' }),
                            h(ElOption, { label: '未生成', value: 'pending' }),
                            h(ElOption, { label: '生成中', value: 'processing' }),
                            h(ElOption, { label: '已生成', value: 'done' }),
                            h(ElOption, { label: '生成失败', value: 'failed' }),
                        ]
                    ),
                ]
            ),

        cellRenderer: ({ rowData }) =>
            h(ElTag, { type: statusType(rowData.status) }, () =>
                statusText(rowData.status)
            ),
    },
    {
        key: 'actions',
        title: '操作',
        width: 100,
        align: 'center',
        fixed: 'right',
        cellRenderer: ({ rowData }) => {
            return h(
                'div',
                {
                    style: `
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        `,
                },
                [// 🎧 “生成配音”按钮
                    h(
                        ElButton,
                        {
                            size: 'small',
                            type: 'primary',
                            disabled: !canGenerate(rowData),
                            onClick: () => generateOne(rowData),
                        },
                        () => '生成配音'
                    ),
                    // ✅ 绿色的 is_done 开关
                    h(ElSwitch, {
                        modelValue: rowData.is_done === 1 ? 'done' : 'undone',
                        activeText: '已完成',
                        inactiveText: '未完成',
                        activeValue: 'done',
                        inactiveValue: 'undone',
                        inlinePrompt: true,
                        size: 'small',
                        style: {
                            '--el-switch-on-color': '#67C23A',  // ✅ 激活时绿色
                            '--el-switch-off-color': '#dcdfe6', // ✅ 未激活灰色
                        },
                        'onUpdate:modelValue': (val) => {
                            const newVal = val === 'done' ? 1 : 0
                            if (rowData.is_done === newVal) return
                            rowData.is_done = newVal
                            console.log('切换台词完成状态:', rowData.is_done)
                            updateLineIsDone(rowData, newVal)
                        },
                    }),


                ]
            )
        },
    }



])


// 1) 如果还不是 reactive，先改成 reactive 数组：
// import 里确保有 reactive / h
// import { reactive, h } from 'vue'

// 假设你原来是：const lineColumns = [ ... ]
// 改成：
// const lineColumns = reactive([ ... ])   // ✅ 让列对象可响应

// 2) 给表头加一个“拖拽手柄”，拖动时修改对应列的 width
function attachResizableHeader(col) {
    const min = col.minWidth ?? 80
    const max = col.maxWidth ?? Infinity
    const origHeader = col.headerCellRenderer

    col.headerCellRenderer = () => h(
        'div',
        { class: 'resizable-header' },
        [
            // 原表头内容保留（有就用，没有就显示标题）
            origHeader ? origHeader() : h('span', col.title),
            // 右侧拖拽手柄
            h('span', {
                class: 'resize-handle',
                onMousedown: (e) => {
                    const startX = e.clientX
                    const startW = Number(col.width ?? min)

                    const onMove = (ev) => {
                        const delta = ev.clientX - startX
                        const next = Math.min(max, Math.max(min, startW + delta))
                        col.width = next  // ✅ 动态改列宽
                    }
                    const onUp = () => {
                        window.removeEventListener('mousemove', onMove)
                        window.removeEventListener('mouseup', onUp)
                    }
                    window.addEventListener('mousemove', onMove)
                    window.addEventListener('mouseup', onUp)
                }
            })
        ]
    )
}

// 3) 指定哪些列可拖（按你的 key 来）
;[
    'role_id', 'text_content', 'emotion_id', 'strength_id',
    'audio', 'edit', 'status', 'actions'
].forEach(k => {
    const c = lineColumns.find(col => col.key === k)
    if (c) {
        c.resizable = true
        attachResizableHeader(c)
    }
})

async function updateLineIsDone(row, val) {
    // ✅ 修正判断逻辑
    if (!row || !row.id) return

    try {
        const res = await lineAPI.updateLine(row.id, {
            chapter_id: row.chapter_id,
            is_done: val,
        })

        if (res?.code === 200) {
            ElMessage.success('台词完成度已更新')
        } else {
            ElMessage.error(res?.message || '台词完成度更新失败')
        }
    } catch (err) {
        console.error('更新台词完成度出错:', err)
        ElMessage.error('请求异常，请稍后重试')
    }
}

import { decodeUtf8OrGbk } from "../utils/utf8-or-gbk.js";
async function handleBatchImport() {
    let loadingInstance = null
    try {
        // 1️⃣ 弹出确认框
        await ElMessageBox.confirm(
            '已存在的章节名不会重复导入，只会导入新的章节！',
            '批量导入章节',
            {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }
        )


        // 3️⃣ 打开文件选择框
        const pickerResult = await window.showOpenFilePicker({
            types: [{ description: '文本文件', accept: { 'text/plain': ['.txt'] } }],
            excludeAcceptAllOption: true,
            multiple: false,
        }).catch(() => null)

        if (!pickerResult || pickerResult.length === 0) {
            ElMessage.info('已取消选择文件')
            return
        }

        const [fileHandle] = pickerResult
        const file = await fileHandle.getFile()
        // ✅ 使用 TextDecoder 解决乱码
        const arrayBuffer = await file.arrayBuffer()
        // ✅ 仅 UTF-8 / GBK 自动识别
        const { encoding, text } = decodeUtf8OrGbk(arrayBuffer);
        console.log('TXT 文件内容:', text)
        // 如果文件内容为空
        if (!text.trim()) {
            ElMessage.warning('TXT 文件为空，未执行导入')
            return
        }

        // 4️⃣ 启动 loading 遮罩
        loadingInstance = ElLoading.service({
            lock: true,
            text: '正在导入章节，请稍候...',
            background: 'rgba(0, 0, 0, 0.4)',
        })

        // 5️⃣ 调用后端导入接口
        const res = await projectAPI.importChapters(projectId, {
            id: projectId,
            content: text,
        })
        if (res?.code === 200) {
            // ✅ 批量导入成功，更新章节列表
            ElMessage.success('TXT 文件已成功导入')

            await loadChapters()
        } else {
            ElMessage.error(res?.message || 'TXT 文件导入失败')
        }

    } catch (err) {
        console.error('❌ 操作取消或出错:', err)
        if (err !== 'cancel') {
            ElMessage.info('已取消导入')
        }
    } finally {
        // 7️⃣ 无论成功或失败都关闭 loading
        if (loadingInstance) {
            loadingInstance.close()
        }
    }
}
import { onBeforeUnmount } from "vue";
const treeHeight = ref(500);
function updateTreeHeight() {
    // 根据窗口大小或 aside 可视区动态调整
    treeHeight.value = window.innerHeight - 230; // 减去头部、搜索框、padding等高度
}

onMounted(() => {
    updateTreeHeight();
    window.addEventListener("resize", updateTreeHeight);
});
onBeforeUnmount(() => {
    window.removeEventListener("resize", updateTreeHeight);
});


// 记忆功能
/**
 * 保存当前项目的最后打开章节
 */
function saveLastChapter() {
    const key = 'lastChapterMap';
    const map = JSON.parse(localStorage.getItem(key) || '{}');
    map[projectId] = activeChapterId.value;
    console.log('保存最后章节', map);
    localStorage.setItem(key, JSON.stringify(map));
}

/**
 * 进入项目时自动恢复上次章节
 */
// 滚动到选中章节
const chapterTreeRef = ref(null)  // ✅ 获取 Tree 实例
function scrollToActiveChapter() {

    if (!chapterTreeRef.value || !activeChapterId.value) return
    chapterTreeRef.value.scrollToNode(activeChapterId.value, 'center')

}
function restoreLastChapter() {
    const key = 'lastChapterMap';
    const map = JSON.parse(localStorage.getItem(key) || '{}');
    const last = map[projectId];

    console.log('恢复最后章节', map, last);
    if (last && chapters.value.find(c => c.id === last)) {
        // 只有当上次选择的章节仍然存在时才恢复
        activeChapterId.value = last;
    } else {
        // 不自动选择章节，让用户手动选择
        activeChapterId.value = null;
    }
    console.log('最终选中章节', activeChapterId.value);
}


</script>

<style scoped>
.filter-bar {
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.filter-select {
    flex: 1;
    max-width: 300px;
    --el-select-input-height: 32px;
    /* 控制高度更紧凑 */
}

.filter-input {
    flex: 1;
    max-width: 240px;
}

.voice-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 16px;
}

.voice-card {
    cursor: pointer;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 140px;
    transition: transform 0.2s ease;
}

.voice-card:hover {
    transform: translateY(-2px);
}

.voice-card-head {
    margin-bottom: 10px;
}

.voice-title {
    font-weight: 600;
    font-size: 15px;
    margin-bottom: 6px;
}

.voice-desc {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    font-size: 13px;
    color: #666;
}

.voice-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}


.page-wrap {
    display: flex;
    flex-direction: column;

    width: 100%;
    /* 承接父级高度（若父级未设，可换成 min-height:100vh） */
    min-height: 0;


}

.header {
    display: flex;
    height: auto;
    width: 100%;
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

    border-radius: 12px;


    /* ✅ 真正滚动层 */
}

.aside {
    height: 92vh;
    padding: 5px;
    background: #fff;
    /* border: 1px red solid; */
    overflow: auto;
}

.aside-head {

    flex-shrink: 0;
    flex-direction: column;
    padding: 10px 12px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    background-color: var(--el-fill-color-light);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.aside-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    /* 左右分布：标题在左，按钮在右 */
    padding: 8px 12px;
    background-color: var(--el-bg-color);
    border-bottom: 1px solid var(--el-border-color-lighter);
    border-radius: 6px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);

    font-weight: 600;
    font-size: 15px;
    color: var(--el-text-color-primary);
    margin-bottom: 12px;
    transition: background-color 0.3s ease;
}

.aside-title:hover {
    background-color: var(--el-fill-color-light);
    /* 悬停时柔和高亮 */
}

.aside-title .title-left {
    display: flex;
    align-items: center;
    gap: 8px;
}

.aside-title .el-icon {
    font-size: 18px;
    color: var(--el-text-color-regular);
    transition: color 0.2s ease;
}

.aside-title:hover .el-icon {
    color: var(--el-color-primary);
}


.aside-actions {
    display: flex;
    align-items: center;
    justify-content: center;
    /* ✅ 居中关键 */
    flex-shrink: 0;
    gap: 10px;
    /* 按钮间距 */
    margin: 10px 0;
    padding: 8px 0;


    border-top: 1px solid var(--el-border-color-lighter);
}

.aside-actions .el-button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;

    font-size: 11px;
    font-weight: 500;
    transition: all 0.2s ease;
}

/* 轻微悬浮动画（增强触感） */
.aside-actions .el-button:hover {
    transform: translateY(-1px);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}


.el-input.mb8 .el-input__wrapper {
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}



/* =============================
   📘 章节菜单最终优化版
   ============================= */

/* =============================
   📘 固定宽度两栏布局版本
   ============================= */
/* 树容器自动撑满剩余空间 */
.tree-container {
    flex: 1;

    overflow: hidden;
}

.chapter-menu {
    border-right: none;

    --transition-fast: 0.18s ease;
    --border-radius: 8px;

}

/* 每个章节项 */
.chapter-item {
    display: flex;
    align-items: center;


    transition: background-color var(--transition-fast), transform 0.1s ease;
}


/* 左侧标题区：固定宽度 */
.chapter-title {
    width: 160px;
    /* ✅ 固定标题宽度 */
    font-size: 15px;
    color: var(--el-text-color-primary);


    transition: color var(--transition-fast);
}

.chapter-item:hover .chapter-title {
    color: var(--el-color-primary);
}

/* 选中 */
.chapter-item.is-active .chapter-title {
    color: var(--el-color-primary);
    font-weight: 600;
    /* ✅ 选中加粗 */
}

/* =============================
   📘 操作区整体
   ============================= */
.chapter-ops {
    width: 0;
    /* ✅ 固定操作宽度 */
    display: flex;
    justify-content: flex-end;
    align-items: center;
    opacity: 0;
    transition: opacity 0.25s ease;
}

/* 悬停或激活显示 */
.chapter-item:hover .chapter-ops,
.chapter-item.is-active .chapter-ops {
    opacity: 1;
}

/* =============================
   🎛 操作按钮样式（非透明版本）
   ============================= */
.op-btn {
    padding: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    background-color: transparent;
    transform: scale(1);
    transition:
        background-color 0.15s ease,
        color 0.15s ease,
        transform 0.15s ease;
}

/* 悬停放大 + 明亮底色 */
.op-btn:hover {
    background-color: #cee8b9;
    /* ✅ 非透明浅蓝底 */
    color: var(--el-color-primary);
    transform: scale(1.12);
}

/* 删除按钮 */
.del-btn {
    color: var(--el-color-danger-light-5);
    background-color: transparent;
}

/* 删除按钮 hover */
.del-btn:hover {
    background-color: #ffecec;
    /* ✅ 非透明浅红底 */
    color: var(--el-color-danger);
    transform: scale(1.12);
}

/* =============================
   🟦 选中状态下（非透明版）
   ============================= */
.chapter-item .op-btn {
    background-color: #cee8b9;
    /* ✅ 纯白底，非透明 */
    box-shadow: 0 0 0 1px var(--el-color-primary-light-5) inset;
}

.chapter-item .del-btn {
    background-color: #fff5f5;
    /* ✅ 纯白微红底 */
    box-shadow: 0 0 0 1px var(--el-color-danger-light-5) inset;
}















.content {

    background: #fff;
    padding: 5px;
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-height: 0;
    /* border: 1px red solid; */


}


.chapter-card {
    flex: 0 0 auto;
    margin-bottom: 1px;

}

.chapter-card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex: 0 0 auto;
    /* 关键：不要抢高度 */
}

.chapter-card-head .left {
    display: flex;
    align-items: center;
    gap: 8px;
}

.chapter-card-head .title {
    font-size: 15px;
    font-weight: 700;
    white-space: nowrap;
    /* 不允许文字换行 */

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
    overflow: auto;
    /* 必须 */
}

.chapter-text {
    white-space: pre-wrap;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    line-height: 1.6;
    color: #333;
    padding: 8px 2px;
}

.el-tabs-box {

    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    min-width: 0;
    min-height: 0;

}


/* 表格容器吃掉剩余高度 */
.toolbar {

    display: flex;
    align-items: center;
    border-bottom: 1px solid #ebeef5;
    background: #fff;
    padding: 0 12px;

}

.table-box {
    position: absolute;
    top: 45px;
    /* ✅ 跟 toolbar 高度一致 */
    bottom: 0;
    left: 0;
    right: 0;

}

.lines-table {
    border-radius: 10px;
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
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: grid;
    /* ✅ 保留 grid */
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
    box-sizing: border-box;
    min-height: 0;
    /* ✅ 防止 flex 塌陷 */
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

.lines-table {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid var(--el-border-color-lighter);
    background: #fff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    font-size: 13px;
}

:deep(.el-table-v2__header) {
    background: #f9fafb;
    font-weight: 600;
    color: #333;
    border-bottom: 1px solid var(--el-border-color-lighter);
}

:deep(.el-table-v2__row) {
    transition: background-color 0.15s ease;
}

:deep(.el-table-v2__row:hover) {
    background-color: #f5f7fa;
}



:deep(.el-tag) {
    border-radius: 6px;
}

:deep(.el-button--small) {
    border-radius: 6px;
}

:deep(.el-textarea__inner) {
    font-size: 13px;
    line-height: 1.4;
    min-height: 60px;
}

:deep(.el-table-v2__cell) {
    padding: 4px 8px;
}

.status-header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 6px 10px;
    background-color: #fafafa;
    border-radius: 6px;
    border: 1px solid #ebeef5;
    transition: all 0.2s ease;
}

.status-header:hover {
    background-color: #f0f6ff;
    border-color: #d0e2ff;
}

.status-title {
    font-weight: 600;
    color: #333;
    font-size: 13px;
    user-select: none;
}

.status-select {
    width: 92px;
    transition: all 0.2s ease;
}

.status-select:hover {
    transform: translateY(-1px);
    box-shadow: 0 0 4px rgba(64, 158, 255, 0.15);
    border-radius: 4px;
}

:deep(.resizable-header) {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    /* 或 space-between，看表头内容 */
    height: 100%;
    padding-right: 6px;
    /* 给手柄留空间 */
    user-select: none;
}

:deep(.resize-handle) {
    position: absolute;
    top: 0;
    right: 0;
    width: 6px;
    height: 100%;
    cursor: col-resize;
}

/* 未选择章节的占位提示 */
.no-chapter-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 400px;
    background: #fafafa;
    border-radius: 12px;
    color: #909399;
}
</style>
