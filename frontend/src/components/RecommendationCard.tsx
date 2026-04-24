type RecommendationCardProps = {
  message: string
  reason?: string
}

export function RecommendationCard({ message, reason }: RecommendationCardProps) {
  return (
    <section>
      <h2>추천</h2>
      <p>{message}</p>
      {reason ? <small>{reason}</small> : null}
    </section>
  )
}
