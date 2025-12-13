// electron/preload.js
const { contextBridge, ipcRenderer } = require('electron')
const path = require('path')
const os = require('os')
console.log('[preload] injected, electron:', process.versions.electron)

// 将绝对路径转换成 file:// URL，跨平台可用
function pathToFileUrl(p) {
  if (!p) return ''
  const isWin = process.platform === 'win32'
  const normalized = isWin ? p.replace(/\\/g, '/') : p
  const prefix = isWin ? 'file:///' : 'file://'
  return prefix + encodeURI(normalized)
}

// 获取用户主目录
function getUserHome() {
  return os.homedir()
}

// 暴露给渲染进程的 API
contextBridge.exposeInMainWorld('native', {
  /**
   * 打开系统文件选择对话框，选音频文件
   * @returns Promise<string|null> 绝对路径，取消时为 null
   */
  pickAudio: () => ipcRenderer.invoke('dialog:pick-audio'),

  /**
   * 把绝对路径转为 file:// URL
   * @param {string} p
   * @returns {string}
   */
  pathToFileUrl,
  // 
  openFolder: (folderPath) => ipcRenderer.invoke('dialog:open-folder', folderPath),
  // 选择音色文件夹
  selectVoiceFolder: () => ipcRenderer.invoke('select-voice-folder'),
  // 选择项目根路径文件夹
  selectDir: () => ipcRenderer.invoke('dialog:selectDir'),
  
  /**
   * 保存文件对话框
   * @param {Object} options - { title, defaultPath, filters }
   * @returns Promise<string|null> 绝对路径，取消时为 null
   */
  saveFile: (options) => ipcRenderer.invoke('dialog:save-file', options),
  
  /**
   * 选择文件对话框
   * @param {Object} options - { title, filters }
   * @returns Promise<string|null> 绝对路径，取消时为 null
   */
  pickFile: (options) => ipcRenderer.invoke('dialog:pick-file', options),
  
  /**
   * 选择目录对话框
   * @param {Object} options - { title }
   * @returns Promise<string|null> 绝对路径，取消时为 null
   */
  pickDirectory: (options) => ipcRenderer.invoke('dialog:pick-directory', options),
  
  /**
   * 获取用户主目录
   * @returns {string}
   */
  getUserHome,
})



