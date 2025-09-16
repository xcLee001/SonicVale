import request from './config'



// 查询单个情绪
export function fetchEmotion(id) {
  return request.get(`/emotions/${id}`).then(res => {
    if (res.code === 200) return res.data
    return null
  })
}

// 查询所有情绪
export function fetchAllEmotions() {
  return request.get(`/emotions`).then(res => {
    if (res.code === 200) return res.data
    return []
  })
}

// 查询单个情绪强度
export function fetchStrength(id) {
  return request.get(`/strengths/${id}`).then(res => {
    if (res.code === 200) return res.data
    return null
  })
}

// 查询所有情绪
export function fetchAllStrengths() {
  return request.get(`/strengths`).then(res => {
    if (res.code === 200) return res.data
    return []
  })
}