import { useEffect } from 'react'
import { wsService } from '../services/websocket'

export function useWebSocket(refresh: () => void, deps: any[] = []) {
  useEffect(() => {
    wsService.connect()
    const unsubs: (() => void)[] = []
    unsubs.push(wsService.on('agent_created', refresh))
    unsubs.push(wsService.on('agent_updated', refresh))
    unsubs.push(wsService.on('agent_deleted', refresh))
    unsubs.push(wsService.on('ticket_created', refresh))
    unsubs.push(wsService.on('ticket_updated', refresh))
    unsubs.push(wsService.on('ticket_deleted', refresh))
    unsubs.push(wsService.on('ticket_assigned', refresh))
    unsubs.push(wsService.on('company_created', refresh))
    unsubs.push(wsService.on('company_deleted', refresh))

    return () => {
      unsubs.forEach((u) => u())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}
