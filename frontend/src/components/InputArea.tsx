import { Send } from 'lucide-react'

interface InputAreaProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  disabled?: boolean
  variant?: 'default' | 'centered'
  placeholder?: string
}

export default function InputArea({
  value,
  onChange,
  onSend,
  disabled,
  variant = 'default',
  placeholder = '输入你的游戏需求...',
}: InputAreaProps) {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  // Centered variant for welcome screen
  if (variant === 'centered') {
    return (
      <div className="w-full">
        <div className="relative">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            className="w-full resize-none border border-gray-300 rounded-xl p-4 pr-14 text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 bg-white shadow-md transition-all duration-200"
            rows={2}
            disabled={disabled}
          />
          <button
            onClick={onSend}
            disabled={disabled || !value.trim()}
            className="absolute right-3 bottom-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white p-2 rounded-lg hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    )
  }

  // Default variant for chat interface
  return (
    <div className="border-t border-gray-200/50 bg-white/90 backdrop-blur-sm shadow-lg">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-end space-x-3">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            className="flex-1 resize-none border border-gray-300 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm transition-all"
            rows={1}
            disabled={disabled}
          />
          <button
            onClick={onSend}
            disabled={disabled || !value.trim()}
            className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-3 rounded-xl hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg disabled:shadow-sm"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}

