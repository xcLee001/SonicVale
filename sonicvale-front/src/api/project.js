// src/api/project.js
import request from './config'
import dayjs from 'dayjs'

// 获取全部项目
export function fetchProjects() {
  return request.get('/projects').then(res => {
    if (res.code === 200) {
      const projects = res.data.map(p => ({
        id: p.id,
        name: p.name,
        description: p.description,
        createdAt: dayjs(p.created_at).format('YYYY-MM-DD HH:mm:ss'),
        updatedAt: dayjs(p.updated_at).format('YYYY-MM-DD HH:mm:ss'),
        createdAtRaw: p.created_at,  // 原始时间戳（排序用）
        updatedAtRaw: p.updated_at,  // 原始时间戳（排序用）
        llmModel: p.llm_model,
        ttsProviderId: p.tts_provider_id,
        ttsLanguage: p.tts_language || 'ZH',
        llmProviderId: p.llm_provider_id,
        promptId: p.prompt_id,
        is_precise_fill: p.is_precise_fill,  // ✅ 新增字段
        project_root_path: p.project_root_path,
      }))

      // 🔥 按更新时间排序（最新在前）
      return projects.sort((a, b) => new Date(b.updatedAtRaw) - new Date(a.updatedAtRaw))
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

// 批量导入章节
export function importChapters(projectId, data) {
  return request.post(`/projects/${projectId}/import`,  data )
}
