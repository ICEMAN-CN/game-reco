import { Message } from './ChatInterface'
import GameCardList from './GameCardList'
import { MessageCircle } from 'lucide-react'

interface MessageListProps {
  messages: Message[]
  onSuggestedQuestionClick?: (question: string) => void
}

export default function MessageList({ messages, onSuggestedQuestionClick }: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map((message, index) => (
        <div
          key={index}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-3xl rounded-2xl px-4 py-3 ${
              message.role === 'user'
                ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/30'
                : 'bg-white/90 backdrop-blur-sm text-gray-800 shadow-lg border border-gray-100/50'
            }`}
          >
            <p className={`whitespace-pre-wrap text-sm leading-relaxed ${
              message.role === 'user' ? 'text-white' : 'text-gray-700'
            }`}>
              {message.content}
            </p>
            {message.games && message.games.length > 0 && (
              <div className="mt-4">
                <GameCardList games={message.games} />
              </div>
            )}
            {/* 后续推荐问题 */}
            {message.suggestedQuestions && message.suggestedQuestions.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200/50">
                <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                  <MessageCircle className="w-3 h-3" />
                  <span>继续探索</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {message.suggestedQuestions.map((question, qIndex) => (
                    <button
                      key={qIndex}
                      onClick={() => onSuggestedQuestionClick?.(question)}
                      className="text-xs px-3 py-1.5 rounded-full bg-gradient-to-r from-blue-50 to-purple-50 text-blue-700 hover:from-blue-100 hover:to-purple-100 border border-blue-100 transition-all duration-200 hover:shadow-md"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

