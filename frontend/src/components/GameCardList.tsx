import { Game } from '../types/game'
import GameCard from './GameCard'

interface GameCardListProps {
  games: Game[]
}

export default function GameCardList({ games }: GameCardListProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {games.map((game) => (
        <GameCard key={game.id} game={game} />
      ))}
    </div>
  )
}

