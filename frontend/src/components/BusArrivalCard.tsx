import { Card } from './ui'

type BusArrivalCardProps = {
  items: Array<{ routeName?: string; route_name?: string; arrivalInMin?: number; arrival_in_min?: number }>
}

function arrivalText(item: BusArrivalCardProps['items'][number]) {
  const minutes = item.arrivalInMin ?? item.arrival_in_min
  return typeof minutes === 'number' ? `${minutes}분 후` : '도착 정보 확인 중'
}

export function BusArrivalCard({ items }: BusArrivalCardProps) {
  return (
    <Card>
      <h2 className='section-title'>버스</h2>
      {items.length === 0 ? (
        <p className='empty-state'>현재 표시할 정보가 없어요</p>
      ) : (
        <ul className='arrival-list'>
          {items.map((item, index) => (
            <li className='arrival-row' key={index}>
              <span className='arrival-name'>{item.routeName ?? item.route_name ?? '버스'}</span>
              <span className='arrival-time'>{arrivalText(item)}</span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
