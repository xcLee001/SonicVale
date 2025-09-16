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
