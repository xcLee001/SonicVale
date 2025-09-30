import request from './config'

export function deleteLinesByChapter(chapterId) {
  return request.delete(`/lines/lines/${chapterId}`)
}
export function getLinesByChapter(chapterId) {
  return request.get(`/lines/lines/${chapterId}`)
}
export function generateAudio(projectId, chapterId, body) {
  console.log('generateAudio', projectId, chapterId, body)
  return request.post(`/lines/generate-audio/${projectId}/${chapterId}`, body)
}
// createLine
// export function getLine(lineId) {
//   // GET /lines/{line_id}
//   return request.get(`/lines/${lineId}`)
// }
export function createLine(projectId, data) {
  // POST /lines/{project_id}
  // data: LineCreateDTO（含 chapter_id, text_content, role_id?, line_order? ...）
  return request.post(`/lines/${projectId}`, data)
}

export function updateLine(lineId, data) {
  // PUT /lines/{line_id}
  // 按你后端的逻辑，不能修改 chapter_id；但如果你传入也会被忽略/校验
  return request.put(`/lines/${lineId}`, data)
}

export function deleteLine(lineId) {
  // DELETE /lines/{line_id}
  return request.delete(`/lines/${lineId}`)
}

export async function reorderLinesByPut(orderList) {
  return request.put('/lines/batch/orders', orderList)
}

// @router.put("/{line_id}/audio_path", response_model=Res[bool])
// def update_line_audio_path(
//         line_id: int,
//     dto: LineCreateDTO,  # 关键：明确从 body 读取“数组”
//     line_service: LineService = Depends(get_line_service),
// ):
export function updateLineAudioPath(lineId, data) {
  // PUT /lines/{line_id}/audio_path
  return request.put(`/lines/${lineId}/audio_path`, data)
}


export function processAudio(line_id, payload) {
  return request.post(`/lines/process-audio/${line_id}`, payload)
}

// 导出结果和字幕
// 导出接口，带 single 参数
export function exportLines(chapter_id, single = false) {
  return request.get(`/lines/export-audio/${chapter_id}`, {
    params: { single }
  })
}


// 矫正字幕
export function correctLines(chapter_id) {
  // POST /lines/correct/{chapter_id}
  return request.post(`/lines/correct-subtitle/${chapter_id}`)
}