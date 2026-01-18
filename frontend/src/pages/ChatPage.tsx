import ChatInterface from '../components/ChatInterface'

export default function ChatPage() {
  return (
    <div className="h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/30">
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-md">
              <span className="text-white font-bold text-lg">GO</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Game Odyssey
              </h1>
              <p className="text-sm text-gray-500">智能游戏推荐助手</p>
            </div>
          </div>
        </div>
      </div>
      <ChatInterface />
    </div>
  )
}

