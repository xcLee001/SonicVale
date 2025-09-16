// logger.js
const log = require('electron-log');
const iconv = require('iconv-lite');

// 保存原始 console（避免丢失）
const raw = { ...console };

// 配置日志
log.transports.file.level = 'silly';   // 全部记录
log.transports.console.level = false;  // 避免重复打印

// 接管 console 方法
['log', 'info', 'warn', 'error'].forEach((level) => {
  console[level] = (...args) => {
    log[level](...args);
    raw[level](...args); // 保持原来在终端里能看到
  };
});

// 中文转码工具（可用于 stdout/stderr）
function decodeText(buffer) {
  let text = buffer.toString('utf8');
  if (/�/.test(text)) {
    text = iconv.decode(buffer, 'gbk');
  }
  return text.trim();
}

module.exports = { log, decodeText };
