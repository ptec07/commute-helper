import { Badge, Card } from './ui'

type RecommendationCardProps = {
  message: string
  reason?: string
}

export function RecommendationCard({ message }: RecommendationCardProps) {
  return (
    <Card className='recommendation-card'>
      <Badge>오늘의 추천</Badge>
      <p className='recommendation-message'>{message}</p>
      <p className='recommendation-reason'>대기 시간이 더 짧습니다.</p>
    </Card>
  )
}
