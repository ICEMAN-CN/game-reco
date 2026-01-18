import { useState } from 'react'
import { Game } from '../types/game'
import { Star, Users } from 'lucide-react'
import { getProxiedImageUrl } from '../utils/imageProxy'

interface GameCardProps {
  game: Game
}

export default function GameCard({ game }: GameCardProps) {
  const [imageError, setImageError] = useState(false)
  // Use horizontal image if available, fallback to cover image
  const originalImageUrl = game.horizontal_image_url || game.cover_image_url
  // Use proxy for external images to avoid CORS issues
  const imageUrl = getProxiedImageUrl(originalImageUrl)

  // Format price display
  const formatPrice = () => {
    if (game.is_free) {
      return <span className="text-green-600 font-semibold text-xs">免费</span>
    }
    if (game.price) {
      const price = typeof game.price === 'string' ? parseFloat(game.price) : game.price
      const originalPrice = game.price_original
        ? typeof game.price_original === 'string'
          ? parseFloat(game.price_original)
          : game.price_original
        : null

      if (originalPrice && originalPrice > price) {
        return (
          <div className="flex items-center gap-1.5">
            <span className="text-gray-400 line-through text-xs">¥{originalPrice}</span>
            <span className="text-red-500 font-semibold text-xs">¥{price}</span>
          </div>
        )
      }
      return <span className="text-gray-800 font-semibold text-xs">¥{price}</span>
    }
    return null
  }

  // Format score display
  const formatScore = () => {
    if (!game.user_score) return null
    const score = typeof game.user_score === 'string' ? parseFloat(game.user_score) : game.user_score
    return score.toFixed(1)
  }

  const handleImageError = () => {
    setImageError(true)
  }

  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-all duration-300 group border border-gray-100/50 hover:border-blue-200">
      {/* Image Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
        {imageUrl && !imageError ? (
          <img
            src={imageUrl}
            alt={game.title}
            className="w-full h-32 object-cover group-hover:scale-110 transition-transform duration-500"
            onError={handleImageError}
            loading="lazy"
          />
        ) : (
          <div className="w-full h-32 bg-gradient-to-br from-blue-100 via-purple-100 to-pink-100 flex items-center justify-center">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-xl">{game.title.charAt(0)}</span>
            </div>
          </div>
        )}

        {/* Score Badge */}
        {formatScore() && (
          <div className="absolute top-2 right-2 bg-black/80 backdrop-blur-md text-white px-2 py-1 rounded-lg flex items-center gap-1 shadow-lg">
            <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
            <span className="text-xs font-semibold">{formatScore()}</span>
          </div>
        )}

        {/* Free Badge */}
        {game.is_free && (
          <div className="absolute top-2 left-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-2 py-1 rounded-lg text-xs font-bold shadow-lg">
            免费游玩
          </div>
        )}
      </div>

      {/* Content Section */}
      <div className="p-4">
        {/* Title and English Title */}
        <h3 className="font-bold text-base text-gray-900 mb-1 line-clamp-1 group-hover:text-blue-600 transition-colors">
          {game.title}
        </h3>
        {game.title_english && (
          <p className="text-xs text-gray-500 mb-2 line-clamp-1">{game.title_english}</p>
        )}

        {/* Description */}
        {game.description && (
          <p className="text-xs text-gray-600 line-clamp-2 mb-3 leading-relaxed">{game.description}</p>
        )}

        {/* Stats Row */}
        <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
          {game.playeds_count && (
            <div className="flex items-center gap-1">
              <Users className="w-3 h-3 text-blue-500" />
              <span className="font-medium">{(game.playeds_count / 10000).toFixed(1)}万人玩过</span>
            </div>
          )}
          {game.developer_name && (
            <span className="truncate text-xs font-medium">{game.developer_name}</span>
          )}
        </div>

        {/* Tags */}
        {game.tags && game.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {game.tags.slice(0, 4).map((tag) => (
              <span
                key={tag}
                className="text-xs bg-gradient-to-r from-blue-50 to-purple-50 text-blue-700 px-2 py-1 rounded-full font-medium border border-blue-100"
              >
                {tag}
              </span>
            ))}
            {game.tags.length > 4 && (
              <span className="text-xs text-gray-400 font-medium">+{game.tags.length - 4}</span>
            )}
          </div>
        )}

        {/* Footer: Platforms and Price */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-200">
          <div className="flex flex-wrap gap-1.5">
            {game.platforms?.slice(0, 3).map((platform) => (
              <span
                key={platform}
                className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-md font-medium"
              >
                {platform}
              </span>
            ))}
          </div>
          <div className="text-right">{formatPrice()}</div>
        </div>
      </div>
    </div>
  )
}

