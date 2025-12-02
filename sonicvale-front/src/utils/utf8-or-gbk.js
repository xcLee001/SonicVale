// utf8-or-gbk.js
export function decodeUtf8OrGbk(arrayBuffer) {
  const u8 = new Uint8Array(arrayBuffer);

  function hasUtf8BOM(bytes) {
    return bytes.length >= 3 && bytes[0] === 0xEF && bytes[1] === 0xBB && bytes[2] === 0xBF;
  }

  function tryDecode(buf, enc, fatal) {
    try {
      const dec = new TextDecoder(enc, fatal ? { fatal: true } : undefined);
      return dec.decode(buf);
    } catch {
      return null;
    }
  }

  // 1) BOM → UTF-8
  if (hasUtf8BOM(u8)) {
    const text = tryDecode(arrayBuffer, "utf-8", false);
    return { encoding: "utf-8", text };
  }

  // 2) 先试 UTF-8（fatal 判非法序列）
  const utf8 = tryDecode(arrayBuffer, "utf-8", true);
  if (utf8 != null) return { encoding: "utf-8", text: utf8 };

  // 3) 回退 GBK
  const gbk = tryDecode(arrayBuffer, "gbk", false);
  if (gbk != null) return { encoding: "gbk", text: gbk };

  // 4) 都不行
  throw new Error("该文件不是 UTF-8 或 GBK 编码，请先转换为 UTF-8/GBK 后再导入。");
}
