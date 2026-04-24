export type CommuteStop = {
  externalId: string
  name: string
  lineName?: string
  kind?: 'bus_stop' | 'subway_station'
  direction?: string
}

export type CommuteProfileInput = {
  name: string
  origin_label: string
  destination_label: string
  target_arrival_time: string
  preferred_mode: string
  walking_tolerance_min: number
}

export type SearchStopsResult = {
  busStops: CommuteStop[]
  subwayStations: CommuteStop[]
}

export type DashboardData = {
  profile: { id: string; name: string; targetArrivalTime: string }
  bus: Array<{ routeName?: string; route_name?: string; arrivalInMin?: number; arrival_in_min?: number }>
  subway: Array<{ lineName?: string; line_name?: string; arrivalInMin?: number; arrival_in_min?: number }>
  recommendation: { mode: string; message: string; reason: string; leaveBy?: string; leave_by?: string }
}
