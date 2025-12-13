import request from './config'

// 创建音色
export function createVoice(payload) {
  // payload: { name, tts_provider_id, reference_path?, description? }
  return request.post('/voices', payload)
}

// 查询单个音色
export function fetchVoice(id) {
  return request.get(`/voices/${id}`).then(res => {
    if (res.code === 200) return res.data
    return null
  })
}

// 查询某个 TTS Provider 下的所有音色
export function fetchVoicesByTTS(tts_provider_id) {
  return request.get(`/voices/tts/${tts_provider_id}`).then(res => {
    if (res.code === 200) return res.data
    return []
  })
}

export function getVoicesByTTS(ttsId = 1) {
  return request.get(`/voices/tts/${ttsId}`)
}



// 更新音色
export function updateVoice(id, payload) {
  return request.put(`/voices/${id}`, payload)
}

// 删除音色
export function deleteVoice(id) {
  return request.delete(`/voices/${id}`)
}

// 导出音色库
export function exportVoices(tts_provider_id, export_path) {
  return request.post('/voices/export', {
    tts_provider_id,
    export_path
  })
}

// 导入音色库
export function importVoices(tts_provider_id, zip_path, target_dir) {
  return request.post('/voices/import', {
    tts_provider_id,
    zip_path,
    target_dir
  })
}

// 处理音色参考音频
export function processVoiceAudio(audio_path, params) {
  return request.post('/voices/process-audio', {
    audio_path,
    speed: params.speed,
    volume: params.volume,
    start_ms: params.start_ms,
    end_ms: params.end_ms,
    silence_sec: params.silence_sec,
    current_ms: params.current_ms
  })
}
