import { Gamepad2 } from 'lucide-react'
import InputArea from './InputArea'

interface WelcomeScreenProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  onDemoClick: (question: string) => void
  disabled?: boolean
}

const DEMO_QUESTIONS = [
  '推荐几个休闲农场类的游戏',
  '有什么好玩的开放世界游戏？',
  '价格便宜但品质上乘的 FPS 游戏',
  '适合新手的 RPG 游戏推荐',
]

export default function WelcomeScreen({
  value,
  onChange,
  onSend,
  onDemoClick,
  disabled,
}: WelcomeScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-80px)] px-4 sm:px-6 lg:px-8 py-12">
      {/* Logo and Title */}
      <div className="flex flex-col items-center mb-8">
        <div className="w-16 h-16 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mb-4 shadow-xl">
          <Gamepad2 className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
          Game Odyssey
        </h1>
        <p className="text-sm text-gray-600 text-center max-w-md">
          智能游戏推荐助手，告诉我你想玩什么类型的游戏
        </p>
      </div>

      {/* Centered Input Area */}
      <div className="w-full max-w-2xl mb-8">
        <InputArea
          value={value}
          onChange={onChange}
          onSend={onSend}
          disabled={disabled}
          variant="centered"
          placeholder="描述你想玩的游戏类型..."
        />
      </div>

      {/* Demo Questions */}
      <div className="w-full max-w-2xl">
        <p className="text-xs text-gray-500 text-center mb-4 font-medium">或者试试这些问题</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {DEMO_QUESTIONS.map((question) => (
            <button
              key={question}
              onClick={() => onDemoClick(question)}
              disabled={disabled}
              className="p-4 text-left bg-white/90 backdrop-blur-sm rounded-xl border border-gray-200 hover:border-blue-400 hover:shadow-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed group hover:bg-gradient-to-br hover:from-blue-50/50 hover:to-purple-50/50"
            >
              <span className="text-sm text-gray-700 group-hover:text-blue-600 transition-colors font-medium">
                {question}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
