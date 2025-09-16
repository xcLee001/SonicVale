// src/api/project.js
import request from './config'
import dayjs from 'dayjs'

// 获取全部项目
export function fetchProjects() {
  return request.get('/projects').then(res => {
    if (res.code === 200) {
      return res.data.map(p => ({
        id: p.id,
        name: p.name,
        description: p.description,
        createdAt: dayjs(p.created_at).format('YYYY-MM-DD'),
        updatedAt: dayjs(p.updated_at).format('YYYY-MM-DD'),
        llmModel: p.llm_model,
        ttsProviderId: p.tts_provider_id,
        llmProviderId: p.llm_provider_id
      }))
    }
    return []
  })
}

// 删除项目
export function deleteProject(id) {
  return request.delete(`/projects/${id}`)
}

// 创建项目
export function createProject(data) {
  return request.post('/projects', data)
}

export function getProjectDetail(projectId) {
  return request.get(`/projects/${projectId}`)
}

export function updateProject(projectId, data) {
  // 后端若是 PATCH 就改为 service.patch
  console.log('updateProject', projectId, data)
  return request.put(`/projects/${projectId}`, data)
}