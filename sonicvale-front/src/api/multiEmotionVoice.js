import request from './config'

export function fetchMultiEmotionVoicesByVoiceId(voiceId) {
  return request.get(`/multi_emotion_voices/voice_id/${voiceId}`)
}

export function createMultiEmotionVoice(dto) {
  return request.post(`/multi_emotion_voices`, dto)
}

export function deleteMultiEmotionVoice(id) {
  return request.delete(`/multi_emotion_voices/${id}`)
}

export function updateMultiEmotionVoice(id, dto) {
    console.log(dto)
  return request.put(`/multi_emotion_voices/${id}`, dto)
}
