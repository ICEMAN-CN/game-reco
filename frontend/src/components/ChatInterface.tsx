import { useState } from 'react'
import MessageList from './MessageList'
import InputArea from './InputArea'
import WelcomeScreen from './WelcomeScreen'
import { chatService } from '../services/chatService'
import { Game } from '../types/game'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  games?: Game[]
  suggestedQuestions?: string[]  // 后续推荐问题
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: messageText,
    }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chatService.chat({ message: messageText })
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        games: response.games,
        suggestedQuestions: response.suggested_questions,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: '抱歉，发生了错误。请稍后重试。',
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleSend = () => {
    sendMessage(input)
  }

  const handleDemoClick = (question: string) => {
    sendMessage(question)
  }

  const hasMessages = messages.length > 0

  // Welcome screen when no messages
  if (!hasMessages) {
    return (
      <WelcomeScreen
        value={input}
        onChange={setInput}
        onSend={handleSend}
        onDemoClick={handleDemoClick}
        disabled={loading}
      />
    )
  }

  // Chat layout when there are messages
  return (
    <div className="flex flex-col h-[calc(100vh-80px)]">
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-5xl mx-auto">
          <MessageList messages={messages} onSuggestedQuestionClick={sendMessage} />
          {loading && (
            <div className="flex justify-start mb-4">
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl px-4 py-3 shadow-lg border border-gray-100">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      <InputArea
        value={input}
        onChange={setInput}
        onSend={handleSend}
        disabled={loading}
      />
    </div>
  )
}

