import request from './config'

export function getRolesByProject(projectId) {
  return request.get(`/roles/project/${projectId}`)
}

export function updateRole(roleId, payload) {
  return request.put(`/roles/${roleId}`, payload)
}

// deleteRole
export function deleteRole(roleId) {
  return request.delete(`/roles/${roleId}`)
}

export function createRole(payload) {
  return request.post('/roles', payload)
}