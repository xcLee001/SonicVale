
const logger = require('./logger');
const { decodeText } = require('./logger');
const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron')
const path = require('path')
const fs = require('fs')
const { spawn, exec } = require('child_process')
const os = require('os')
const http = require('http')


let backendProcess = null

function startBackend() {
  const isDev = !app.isPackaged
  const exePath = isDev
    ? path.join(__dirname, 'main.exe') // dev 环境路径
    : path.join(process.resourcesPath, 'app.asar.unpacked', 'electron', 'main.exe') // prod 路径

  console.log('启动后端：', exePath)

  backendProcess = spawn(exePath, [], {
    cwd: path.dirname(exePath),
    detached: true,  // ❗关闭主进程时能跟着退出
    stdio: ['ignore', 'pipe', 'pipe'], // 输出日志供调试
  })

  // 日志输出（可选）
  backendProcess.stdout.on('data', data => {
    console.log(`[后端] ${decodeText(data)}`);
  });

  backendProcess.stderr.on('data', data => {
    console.error(`[后端错误] ${decodeText(data)}`);
  });

  backendProcess.on('exit', (code, signal) => {
    console.log(`后端退出，code=${code}, signal=${signal}`);
  });
}

function waitForBackendReady(retries = 60, delay = 500) {
  return new Promise((resolve, reject) => {
    let attempts = 0
    const check = () => {
      const req = http.get('http://127.0.0.1:8200/docs', res => {
        res.destroy()
        resolve(true)
      }).on('error', err => {
        if (++attempts >= retries) reject(err)
        else setTimeout(check, delay)
      })
    }
    check()
  })
}

function createWindow() {
  const win = new BrowserWindow({

    width: 1360,
    height: 765,
    show: false, // ✅ 先不显示，等最大化后再显示
    icon: path.join(__dirname, '../resource/icon/yingu.ico'),

    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
      webSecurity: false,
    },
    autoHideMenuBar: true, // 这会让菜单栏自动隐藏，但通过 Alt 可以唤出

  })

  win.once('ready-to-show', () => {
    win.maximize() // ✅ 启动时自动最大化（不是全屏）
    win.show()     // ✅ 再显示窗口
  })
  const isDev = !app.isPackaged
  if (isDev) {
    // 开发环境：直连 Vite
    win.loadURL('http://localhost:5173')
    // win.webContents.openDevTools({ mode: 'detach' })
  } else {
    // 生产环境：直接加载打包后的静态文件，不阻塞首屏
    win.loadFile(path.join(__dirname, '../dist/index.html'))

    // 非阻塞地检测后端是否就绪，用于日志/提示
    waitForBackendReady()
      .then(() => console.log('后端就绪'))
      .catch(e => {
        console.error('后端未就绪:', e)
        // 可选：给用户一个友好提示页（不想覆盖 UI 就注释掉下面两行）
        mainWindow.loadURL('data:text/html,<h1 style="font-family:sans-serif">backend is not ready</h1><p>please restart now</p>')
      })
  }
}

// ============== 事件入口 ===============

app.whenReady().then(async () => {
  startBackend()
  try {
    await waitForBackendReady()
    createWindow()
  } catch (err) {
    console.error('后端启动失败:', err)
    const errorWin = new BrowserWindow({ width: 600, height: 300 })
    errorWin.loadURL(`data:text/html;charset=utf-8,
  <!DOCTYPE html>
  <html>
    <head><meta charset="UTF-8"></head>
    <body>
      <h2 style="font-family:sans-serif">后端启动失败</h2>
      <p>请检查后端程序并重启应用</p>
    </body>
  </html>
`);
  }
})

// 杀死后端
function killBackendTree(child) {
  if (!child || !child.pid) return
  const pid = child.pid

  if (process.platform === 'win32') {
    exec(`taskkill /PID ${pid} /T /F`, (err) => {
      if (err) console.warn('taskkill 失败：', err.message)
    })
  } else {
    try {
      // 先温柔地
      process.kill(pid, 'SIGTERM')
      // 兜底：0.8s 后还活着就强杀整个进程组
      setTimeout(() => {
        try { process.kill(-pid, 'SIGKILL') } catch { }
        try { process.kill(pid, 'SIGKILL') } catch { }
      }, 800)
    } catch (e) {
      // 可能已退出
    }
  }

}
function shutdown() {
  killBackendTree(backendProcess)
}
app.on('before-quit', shutdown)
app.on('will-quit', shutdown)
app.on('quit', shutdown)

app.on('window-all-closed', () => {
  shutdown()
  if (process.platform !== 'darwin') app.quit()
})

// 处理 Ctrl+C / 任务管理器结束 等
process.on('SIGINT', shutdown)
process.on('SIGTERM', shutdown)
process.on('exit', shutdown)


// ============== IPC 处理 ===============
// 选择参考音频
ipcMain.handle('dialog:pick-audio', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    title: '选择参考音频',
    properties: ['openFile'],
    filters: [
      { name: 'Audio', extensions: ['mp3', 'wav', 'm4a', 'ogg', 'flac'] }
    ]
  })

  if (canceled || !filePaths || !filePaths[0]) return null
  return filePaths[0] // 返回绝对路径
})

// 打开文件夹
ipcMain.handle('dialog:open-folder', async (event, folderPath) => {
  if (!folderPath) return

  try {
    await shell.openPath(folderPath)
    return true
  } catch (e) {
    console.error('打开文件夹失败', e)
    return false
  }
})

//选择音色文件夹
ipcMain.handle('select-voice-folder', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory']
  })
  if (result.canceled || result.filePaths.length === 0) return null

  const rootPath = result.filePaths[0]
  const folders = fs.readdirSync(rootPath, { withFileTypes: true }).filter(dirent => dirent.isDirectory())

  const resultList = []

  for (const folder of folders) {
    const emotion = folder.name
    const emotionPath = path.join(rootPath, emotion)
    const files = fs.readdirSync(emotionPath)

    for (const file of files) {
      const strength = path.parse(file).name
      const reference_path = path.join(emotionPath, file)

      resultList.push({
        voice_name: path.basename(rootPath),
        emotion_name: emotion,
        strength_name: strength,
        reference_path
      })
    }
  }

  return resultList
})


// ✅ 选择文件夹：返回选中的绝对路径
ipcMain.handle('dialog:selectDir', async () => {
  const result = await dialog.showOpenDialog({
    title: '选择项目根路径',
    properties: ['openDirectory', 'createDirectory']
  })
  if (result.canceled || !result.filePaths || !result.filePaths.length) return null
  return result.filePaths[0]
})

// 保存文件对话框
ipcMain.handle('dialog:save-file', async (event, options) => {
  const { title, defaultPath, filters } = options || {}
  const result = await dialog.showSaveDialog({
    title: title || '保存文件',
    defaultPath: defaultPath || '',
    filters: filters || [{ name: '所有文件', extensions: ['*'] }]
  })
  if (result.canceled || !result.filePath) return null
  return result.filePath
})

// 选择文件对话框
ipcMain.handle('dialog:pick-file', async (event, options) => {
  const { title, filters } = options || {}
  const result = await dialog.showOpenDialog({
    title: title || '选择文件',
    properties: ['openFile'],
    filters: filters || [{ name: '所有文件', extensions: ['*'] }]
  })
  if (result.canceled || !result.filePaths || !result.filePaths.length) return null
  return result.filePaths[0]
})

// 选择目录对话框
ipcMain.handle('dialog:pick-directory', async (event, options) => {
  const { title } = options || {}
  const result = await dialog.showOpenDialog({
    title: title || '选择目录',
    properties: ['openDirectory', 'createDirectory']
  })
  if (result.canceled || !result.filePaths || !result.filePaths.length) return null
  return result.filePaths[0]
})

// 写入文件（用于音频下载等）
ipcMain.handle('fs:write-file', async (event, { filePath, data }) => {
  try {
    // data 是 Uint8Array 转成的普通数组，需要转回 Buffer
    const buffer = Buffer.from(data)
    fs.writeFileSync(filePath, buffer)
    return { success: true }
  } catch (error) {
    console.error('写入文件失败:', error)
    return { success: false, error: error.message }
  }
})

// 复制文件（用于音频下载等）
ipcMain.handle('fs:copy-file', async (event, { sourcePath, destPath }) => {
  try {
    fs.copyFileSync(sourcePath, destPath)
    return { success: true }
  } catch (error) {
    console.error('复制文件失败:', error)
    return { success: false, error: error.message }
  }
})

