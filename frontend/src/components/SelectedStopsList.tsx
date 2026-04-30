type SelectedStopsListProps = {
  items: Array<{ externalId: string; name: string; lineName?: string }>
}

export function SelectedStopsList({ items }: SelectedStopsListProps) {
  return (
    <section className='card'>
      <h2 className='section-title'>선택한 곳</h2>
      {items.length === 0 ? (
        <p className='empty-state'>아직 선택한 곳이 없어요</p>
      ) : (
        <>
          <p className='success-note' role='status'>선택 완료</p>
          <ul className='selected-list'>
            {items.map((item) => (
              <li className='chip' key={item.externalId}>
                {item.name}
                {item.lineName ? <span className='tiny'>{item.lineName}</span> : null}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
