type BusArrivalCardProps = {
  items: Array<{ routeName?: string; route_name?: string; arrivalInMin?: number; arrival_in_min?: number }>
}

export function BusArrivalCard({ items }: BusArrivalCardProps) {
  return (
    <section>
      <h2>버스</h2>
      {items.length === 0 ? (
        <p>현재 표시할 버스 도착 정보가 없습니다.</p>
      ) : (
        <ul>
          {items.map((item, index) => (
            <li key={index}>{item.routeName ?? item.route_name ?? '버스'} </li>
          ))}
        </ul>
      )}
    </section>
  )
}
