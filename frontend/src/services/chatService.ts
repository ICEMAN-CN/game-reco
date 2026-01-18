import api from './api'
import { Game } from '../types/game'

export interface ChatRequest {
  message: string
  stream?: boolean
}

export interface ChatResponse {
  response: string
  games?: Game[]
  suggested_questions?: string[]  // 后续推荐问题
}

export const chatService = {
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/chat', request)
    return response.data
  },
}

