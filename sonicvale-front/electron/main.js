const logger = require('./logger');
const { decodeText } = require('./logger');
const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron')
const path = require('path')
const fs = require('fs')
const { spawn, exec } = require('child_process')
const os = require('os')
const http = require('http')

let backendProcess = null
let mainWindow = null

function startBackend() {
  const isDev = !app.isPackaged

  // 在开发模式下，不启动后端进程
  if (isDev) {
    console.log('开发模式：跳过后端启动');
    return;
  }

  const exeName = process.platform === 'win32' ? 'main.exe' : 'main';
  const exePath = path.join(process.resourcesPath, 'app.asar.unpacked', 'electron', exeName);

  console.log('启动后端：', exePath);

  // 检查文件是否存在
  if (!fs.existsSync(exePath)) {
    console.error(`错误：可执行文件不存在于 ${exePath}`);
    throw new Error(`可执行文件不存在: ${exePath}`);
  }

  // 在非 Windows 系统上设置执行权限
  if (process.platform !== 'win32') {
    try {
      fs.chmodSync(exePath, 0o755); // 添加执行权限
      console.log('已为可执行文件设置执行权限');
    } catch (err) {
      console.warn(`无法设置执行权限: ${err.message}`);
    }
  }

  backendProcess = spawn(exePath, [], {
    cwd: path.dirname(exePath),
    detached: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  // 日志输出
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
  const isDev = !app.isPackaged

  mainWindow = new BrowserWindow({
    width: 1500,
    height: 800,
    icon: path.join(__dirname, '../resource/icon/yingu.icns'), // 使用 macOS 图标格式
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
      webSecurity: false,
      allowRunningInsecureContent: true, // 允许运行不安全内容
    },
    autoHideMenuBar: true,
    show: false, // 初始不显示，等待内容加载完成
  })

  // 添加窗口事件监听
  mainWindow.once('ready-to-show', () => {
    console.log('窗口准备就绪，显示窗口');
    mainWindow.show();

    // 开发模式下自动打开开发者工具
    if (isDev) {
      mainWindow.webContents.openDevTools({ mode: 'detach' });
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  if (isDev) {
    // 开发环境：直连 Vite
    console.log('加载开发服务器: http://localhost:5173');
    mainWindow.loadURL('http://localhost:5173')
        .then(() => console.log('页面加载成功'))
        .catch(err => console.error('页面加载失败:', err));
  } else {
    // 生产环境：加载打包后的静态文件
    console.log('加载生产文件');
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
        .then(() => console.log('生产文件加载成功'))
        .catch(err => console.error('生产文件加载失败:', err));
  }
}

// ============== 事件入口 ===============

app.whenReady().then(async () => {
  console.log('Electron 应用准备就绪');

  const isDev = !app.isPackaged

  if (isDev) {
    // 开发模式：直接创建窗口，不等待后端
    console.log('开发模式：直接创建窗口');
    createWindow();
  } else {
    // 生产模式：启动后端并等待
    try {
      startBackend();
      await waitForBackendReady();
      createWindow();
    } catch (err) {
      console.error('后端启动失败:', err);
      const errorWin = new BrowserWindow({ width: 600, height: 300 });
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
  }
})

app.on('activate', () => {
  // 在 macOS 上，当点击 dock 图标时，如果没有打开的窗口，则重新创建一个
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

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
  const isDev = !app.isPackaged
  if (!isDev && backendProcess) {
    killBackendTree(backendProcess)
  }
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