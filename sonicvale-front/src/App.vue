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
        <div class="info-item">版本：v1.1.0</div>
        <div class="info-item">配音交流群：575715633（如果群已经满，请按照申请提示进入其他群）</div>
        <!-- 🔔 醒目声明 -->
        <div class="info-warning">
          
            本软件完全免费，遵循 AGPLv3 开源协议。
       
            禁止倒卖，违者必究。 
          
        </div>
      </div>



      <!-- 底部收缩/展开按钮 -->
      <div class="sider-footer">
        <el-tooltip :content="collapsed ? '展开菜单' : '收起菜单'" placement="right">
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
          <span v-if="!collapsed" class="collapse-label">收起侧边栏</span>
        </transition>
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
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Folder, Setting, Microphone, Fold, Expand, Document } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = ref(route.path)
watch(() => route.path, (p) => (activeMenu.value = p))

const collapsed = ref(false)
const toggleCollapse = () => { collapsed.value = !collapsed.value }
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
  background: #1f2d3d;
  color: #fff;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  transition: width .2s ease;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

/* 顶部 Logo */
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 60px;
  padding: 0 12px;
  background: #15202b;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.logo-emoji {
  font-size: 18px;
  line-height: 1;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
}

/* 菜单区域：只纵向滚动，禁止横向滚动（修复折叠态横向滚动条） */
.sider-menu {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 底部控制区 */
.sider-footer {
  flex: 0 0 56px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  padding: 10px 8px 12px 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.is-collapsed .sider-footer {
  justify-content: center;
}

/* 折叠按钮 */
.collapse-btn {
  background: rgba(255, 255, 255, 0.06);
  border: none;
  width: 36px;
  height: 36px;
  backdrop-filter: blur(2px);
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.12);
}

.collapse-label {
  font-size: 12px;
  color: #bfcbd9;
}

/* 右侧容器 */
.layout-content {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.layout-main {
  background: #f5f7fa;
  padding: 24px;
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
}

/* —— 菜单样式（展开态） —— */
.el-menu-item {
  border-radius: 8px;
  margin: 4px 12px;
}

.el-menu-item:hover {
  background-color: #304156 !important;
}

.el-menu-item.is-active {
  background-color: #409EFF !important;
  color: #fff !important;
}

/* —— 折叠态定制（关键修复） —— */
.el-menu--collapse .el-menu-item {
  margin: 6px;
  /* 避免原 12px 横向外边距导致 64px 溢出 */
  padding: 0;
  width: auto;
  box-sizing: border-box;
  justify-content: center;
}

.el-menu--collapse .el-menu-item .el-icon {
  margin-right: 0;
}

.el-menu--collapse .el-menu-item.is-active {
  border-radius: 10px;
}

/* 如果后续加子菜单，折叠时隐藏箭头避免溢出 */
.el-menu--collapse .el-sub-menu__icon-arrow {
  display: none;
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
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 13px;
  line-height: 1.6;
  background: rgba(255, 255, 255, 0.02);
  color: #c9d4e0;
}

/* 普通信息行（版本、联系方式） */
.info-item {
  color: #aeb8c5;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-item:first-child {
  font-weight: 600;
  color: #d6dee8;
}

/* 让QQ号可选中复制 */
.info-item::selection {
  background: #409eff;
  color: #fff;
}



.info-warning {
  margin-top: 8px;
  padding: 8px 10px;
  font-size: 12px;
  color: #ffb84d;
  background: rgba(255, 184, 77, 0.1);
  border: 1px solid rgba(255, 184, 77, 0.25);
  border-radius: 6px;
  line-height: 1.5;
  text-align: justify;
  transition: all 0.3s ease;
}

.info-warning:hover {
  background: rgba(255, 184, 77, 0.2);
  color: #ffd27f;
}
</style>
