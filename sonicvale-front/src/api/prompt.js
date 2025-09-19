import request from './config'

export function createPrompt(data) {
  return request.post('/prompts/', data)
}
export async function fetchPromptList() {
  const res = await request.get('/prompts/')
    if (res.code === 200) {
        return res.data
    }
    return []
}
export async function fetchPromptById(id) {
    const res = await request.get(`/prompts/${id}`)
    if (res.code === 200) {
        return res.data
    }
    return null
    }
export function updatePrompt(id, data) {
  return request.put(`/prompts/${id}`, data)
}
export function deletePrompt(id) {
  return request.delete(`/prompts/${id}`)
}
// 获取所有task
export function fetchAllTasks() {
  return request.get('/prompts/tasks/all')
  .then(res => {
    if (res.code === 200) {
      return res.data
    }
    return []
  })
}
