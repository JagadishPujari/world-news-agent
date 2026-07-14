import axios, { AxiosInstance } from 'axios'

// FastAPI backend endpoint. Configure VITE_API_BASE_URL when the backend is
// hosted elsewhere (e.g. production deployment).
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

export const getApiClient = () => {
  return apiClient
}

export const chat = async (
  sessionId: string,
  message: string,
  preferences?: any
) => {
  const response = await getApiClient().post('/api/chat', {
    session_id: sessionId,
    message,
    preferences,
  })
  return response.data
}

export const generateDigest = async (
  sessionId: string,
  topics?: string[],
  style?: string
) => {
  const response = await getApiClient().post('/api/digest', {
    session_id: sessionId,
    topics,
    style,
  })
  return response.data
}

export const simplifyContent = async (
  sessionId: string,
  content: string,
  url?: string,
  level?: string
) => {
  const response = await getApiClient().post('/api/simplify', {
    session_id: sessionId,
    content,
    url,
    level,
  })
  return response.data
}

export const getHealth = async () => {
  const response = await getApiClient().get('/api/health')
  return response.data
}
