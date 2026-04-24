type SelectedStopsListProps = {
  items: Array<{ externalId: string; name: string; lineName?: string }>
}

export function SelectedStopsList({ items }: SelectedStopsListProps) {
  if (items.length === 0) {
    return <p>선택된 정류장/역이 없습니다.</p>
  }

  return (
    <ul>
      {items.map((item) => (
        <li key={item.externalId}>{item.name}</li>
      ))}
    </ul>
  )
}
