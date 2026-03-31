<template>
  <el-container class="layout-root">
    <!-- 侧边栏 -->
    <el-aside class="layout-sider" :class="{ 'is-collapsed': collapsed }" :width="collapsed ? '64px' : '220px'">
      <!-- Logo -->
      <div class="logo">
        <span class="logo-emoji">🎙️</span>
        <transition name="fade">
          <span v-if="!collapsed" class="logo-text">音谷配音平台</span>
        </transition>
      </div>

      <!-- 菜单 -->
      <el-menu :default-active="activeMenu" background-color="#1f2d3d" text-color="#bfcbd9" active-text-color="#409EFF"
        router class="sider-menu" :collapse="collapsed" collapse-transition>
        <el-menu-item index="/projects">
          <el-icon>
            <Folder />
          </el-icon><span>内容管理</span>
        </el-menu-item>
        <el-menu-item index="/voices">
          <el-icon>
            <Microphone />
          </el-icon><span>音色管理</span>
        </el-menu-item>
        <el-menu-item index="/config">
          <el-icon>
            <Setting />
          </el-icon><span>配置中心</span>
        </el-menu-item>
        <!-- 提示 -->
        <el-menu-item index="/prompts">
          <el-icon>
            <Document />
          </el-icon><span>提示词管理</span>
        </el-menu-item>
      </el-menu>

      <!-- ✅ 新增底部信息 -->
      <!-- 底部信息（版本/免费/联系方式） -->
      <!-- 警告： -->
      <!--
  ================================================================
  🎙️ 音谷配音平台
  作者：lxc

  QQ：1428390267
  本软件完全免费
  ================================================================
-->

      <div class="sider-info" v-if="!collapsed">
        <div class="info-item">版本：v1.1.4</div>
        <div class="info-item">配音交流群：1080986764（如果群已经满，请按照申请提示进入其他群）</div>
        <!-- 🔔 醒目声明 -->
        <div class="info-warning">
          
            本软件完全免费，遵循 AGPLv3 开源协议。
       
            禁止倒卖，违者必究。 
          
        </div>
      </div>



      <!-- 底部收缩/展开按钮 -->
      <div class="sider-footer">
        <!-- 主题切换 -->
        <div class="footer-item">
          <el-tooltip :content="isDark ? '切换到亮色模式' : '切换到暗色模式'" placement="right" :disabled="!collapsed">
            <el-button class="theme-btn" circle @click="toggleTheme">
              <el-icon v-if="isDark">
                <Sunny />
              </el-icon>
              <el-icon v-else>
                <Moon />
              </el-icon>
            </el-button>
          </el-tooltip>
          <transition name="fade">
            <span v-if="!collapsed" class="action-label" @click="toggleTheme">{{ isDark ? '暗色模式' : '亮色模式' }}</span>
          </transition>
        </div>

        <!-- 折叠切换 -->
        <div class="footer-item">
          <el-tooltip :content="collapsed ? '展开菜单' : '收起菜单'" placement="right" :disabled="!collapsed">
            <el-button class="collapse-btn" circle @click="toggleCollapse">
              <el-icon v-if="collapsed">
                <Expand />
              </el-icon>
              <el-icon v-else>
                <Fold />
              </el-icon>
            </el-button>
          </el-tooltip>
          <transition name="fade">
            <span v-if="!collapsed" class="action-label" @click="toggleCollapse">收起侧边栏</span>
          </transition>
        </div>
      </div>
    </el-aside>

    <!-- 右侧内容 -->
    <el-container class="layout-content">
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Folder, Setting, Microphone, Fold, Expand, Document, Moon, Sunny } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = ref(route.path)
watch(() => route.path, (p) => (activeMenu.value = p))

const collapsed = ref(false)
const toggleCollapse = () => { collapsed.value = !collapsed.value }

const THEME_KEY = 'sv_theme'
const isDark = ref(false)

function readStoredTheme() {
  try { return localStorage.getItem(THEME_KEY) } catch { return null }
}

function systemPrefersDark() {
  try { return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches } catch { return false }
}

function applyTheme(dark) {
  document.documentElement.classList.toggle('dark', !!dark)
}

function toggleTheme() {
  isDark.value = !isDark.value
}

onMounted(() => {
  const stored = readStoredTheme()
  isDark.value = stored ? stored === 'dark' : systemPrefersDark()
  applyTheme(isDark.value)
})

watch(isDark, (dark) => {
  applyTheme(dark)
  try { localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light') } catch { }
  window.dispatchEvent(new CustomEvent('sv-theme-changed', { detail: { theme: dark ? 'dark' : 'light' } }))
})
</script>

<style>
/* —— 基础布局 —— */
html,
body,
#app {
  height: 100%;
  margin: 0;
  overflow: hidden;
}

.layout-root {
  height: 100vh;
}

.layout-sider {
  background: linear-gradient(180deg, #1a2634 0%, #1f2d3d 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden !important;
  transition: width .2s ease;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
}

/* 折叠态强制隐藏所有滚动条 */
.layout-sider.is-collapsed {
  overflow: hidden !important;
}

.layout-sider.is-collapsed * {
  overflow: hidden !important;
}

/* 顶部 Logo */
.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 60px;
  padding: 0 12px;
  background: linear-gradient(135deg, #15202b 0%, #1a2836 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.is-collapsed .logo {
  padding: 0;
}

.logo-emoji {
  font-size: 22px;
  line-height: 1;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.logo-text {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  background: linear-gradient(90deg, #fff, #a8d8ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 菜单区域：只纵向滚动，禁止横向滚动（修复折叠态横向滚动条） */
.sider-menu {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  border: none !important;
}

/* 修复折叠时菜单容器溢出 */
.is-collapsed .sider-menu {
  overflow: hidden;
}

/* 底部控制区 */
.sider-footer {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.1);
}

.is-collapsed .sider-footer {
  align-items: center;
  padding: 12px 0;
  width: 64px;
  box-sizing: border-box;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 44px;
  padding: 0 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.footer-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.is-collapsed .footer-item {
  justify-content: center;
  padding: 0;
  width: 56px;
  height: 44px;
  margin: 0 auto;
}

.action-label {
  font-size: 13px;
  color: #bfcbd9;
  white-space: nowrap;
  user-select: none;
  transition: color 0.2s ease;
}

.footer-item:hover .action-label {
  color: #fff;
}

/* 折叠按钮 */
.collapse-btn {
  background: rgba(255, 255, 255, 0.08);
  border: none;
  width: 36px;
  height: 36px;
  backdrop-filter: blur(4px);
  transition: all 0.25s ease;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(64, 158, 255, 0.3);
  transform: scale(1.05);
}

/* 主题切换按钮 */
.theme-btn {
  background: rgba(255, 255, 255, 0.08);
  border: none;
  width: 36px;
  height: 36px;
  backdrop-filter: blur(4px);
  transition: all 0.25s ease;
  flex-shrink: 0;
}

.theme-btn:hover {
  background: rgba(255, 184, 77, 0.3);
  transform: scale(1.05);
}

/* 右侧容器 */
.layout-content {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.layout-main {
  background: var(--el-bg-color-page);
  padding: 24px;
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
}

/* —— 菜单样式（展开态） —— */
.el-menu-item {
  border-radius: 10px;
  margin: 4px 12px;
  height: 44px;
  line-height: 44px;
  transition: all 0.25s ease;
}

.el-menu-item .el-icon {
  font-size: 18px;
  transition: transform 0.2s ease;
}

.el-menu-item:hover .el-icon {
  transform: scale(1.1);
}

.el-menu-item:hover {
  background-color: rgba(64, 158, 255, 0.15) !important;
}

.el-menu-item.is-active {
  background: linear-gradient(135deg, #409EFF 0%, #5cadff 100%) !important;
  color: #fff !important;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.35);
}

/* —— 折叠态定制（关键修复） —— */
.el-menu--collapse .el-menu-item {
  margin: 6px 8px;
  padding: 0 !important;
  width: 48px !important;
  min-width: 48px !important;
  max-width: 48px !important;
  height: 48px;
  box-sizing: border-box;
  justify-content: center;
  display: flex;
  align-items: center;
}

.el-menu--collapse .el-menu-item .el-icon {
  margin-right: 0;
  font-size: 20px;
}

.el-menu--collapse .el-menu-item.is-active {
  border-radius: 12px;
}

/* 如果后续加子菜单，折叠时隐藏箭头避免溢出 */
.el-menu--collapse .el-sub-menu__icon-arrow {
  display: none;
}

/* 折叠态菜单容器修复溢出 */
.el-menu--collapse {
  width: 64px !important;
  min-width: 64px !important;
  max-width: 64px !important;
  overflow: hidden !important;
}

/* el-aside 内部滚动条强制隐藏 */
.is-collapsed .el-menu {
  overflow: hidden !important;
}

/* 隐藏 webkit 滚动条 */
.is-collapsed ::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity .15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}


/* 底部信息块 */
/* 底部信息块整体 */
.sider-info {
  flex: 0 0 auto;
  padding: 12px 14px 14px 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 12px;
  line-height: 1.6;
  background: rgba(0, 0, 0, 0.15);
  color: #c9d4e0;
}

/* 普通信息行（版本、联系方式） */
.info-item {
  color: #9aa8b8;
  margin-bottom: 6px;
  display: flex;
  align-items: flex-start;
  gap: 4px;
  word-break: break-all;
}

.info-item:first-child {
  font-weight: 600;
  color: #67c23a;
  font-size: 13px;
}

/* 让QQ号可选中复制 */
.info-item::selection {
  background: #409eff;
  color: #fff;
}

.info-warning {
  margin-top: 10px;
  padding: 10px 12px;
  font-size: 11px;
  color: #ffb84d;
  background: linear-gradient(135deg, rgba(255, 184, 77, 0.12) 0%, rgba(255, 152, 0, 0.08) 100%);
  border: 1px solid rgba(255, 184, 77, 0.3);
  border-radius: 8px;
  line-height: 1.6;
  text-align: justify;
  transition: all 0.3s ease;
}

.info-warning:hover {
  background: linear-gradient(135deg, rgba(255, 184, 77, 0.2) 0%, rgba(255, 152, 0, 0.15) 100%);
  color: #ffd27f;
  border-color: rgba(255, 184, 77, 0.5);
}
</style>
