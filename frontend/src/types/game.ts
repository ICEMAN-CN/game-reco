export interface Game {
  id: number
  external_id: number
  title: string
  title_english?: string
  developer_name?: string
  publisher_name?: string
  description?: string
  description_html?: string
  cover_image_url?: string
  thumbnail_url?: string
  horizontal_image_url?: string
  platforms?: string[]
  platform_ids?: number[]
  publish_date?: string
  publish_timestamp?: number
  user_score?: string | number
  score_users_count?: number
  playeds_count?: number
  want_plays_count?: number
  tags?: string[]
  steam_game_id?: string
  steam_praise_rate?: number
  steam_header_image?: string
  is_free: boolean
  price?: string | number
  price_original?: string | number
  device_requirement_html?: string
  theme_color?: string
  hot_value?: number
  be_official_chinese_enable?: boolean
  play_hours_caption?: string
  real_players_score?: number
  real_players_count?: number
  source?: string
  raw_data?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

