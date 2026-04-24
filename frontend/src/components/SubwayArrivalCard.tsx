type SubwayArrivalCardProps = {
  items: Array<{ lineName?: string; line_name?: string; arrivalInMin?: number; arrival_in_min?: number }>
}

export function SubwayArrivalCard({ items }: SubwayArrivalCardProps) {
  return (
    <section>
      <h2>지하철</h2>
      <ul>
        {items.map((item, index) => (
          <li key={index}>{item.lineName ?? item.line_name ?? '지하철'}</li>
        ))}
      </ul>
    </section>
  )
}
