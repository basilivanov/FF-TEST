import React, { useMemo } from 'react'
import Mermaid from '@/components/Mermaid'
import { formatRole } from '@/lib/format'

type Status = 'NEW'|'RUNNING'|'DONE'|'FAILED'|'WAIT_BUDGET'|'RETRYABLE'|string

export interface FlightTaskLike {
  role: string
  status: Status
}

export interface FlightRunLike {
  status: Status
}

interface FeatureFlightMapProps {
  tasks: FlightTaskLike[]
  runs?: FlightRunLike[]
}

const STAGES = ['Dev','watchdog','Gate','QA','Scribe','Apply'] as const

export const FeatureFlightMap: React.FC<FeatureFlightMapProps> = ({ tasks, runs }) => {
  const roleStatus: Record<string, Status> = useMemo(() => {
    const map: Record<string, Status> = {}
    for (const t of tasks) {
      if (!t?.role) continue
      // При наличии нескольких задач по роли — берём «худший» статус
      const prev = map[t.role]
      if (!prev) { map[t.role] = t.status; continue }
      const order: Status[] = ['FAILED','RUNNING','WAIT_BUDGET','RETRYABLE','NEW','DONE']
      const a = order.indexOf(String(t.status).toUpperCase() as Status)
      const b = order.indexOf(String(prev).toUpperCase() as Status)
      map[t.role] = a < b ? t.status : prev
    }
    return map
  }, [tasks])

  const chart = useMemo(() => {
    const labels = STAGES.map(s => {
      if (s === 'watchdog') return `${s}[Watchdog]`
      return `${s}[${formatRole(s)}]`
    }).join('\n')
    const edges = STAGES.slice(0, -1).map((s, i) => `${s} --> ${STAGES[i+1]}`).join('\n')

    const classDefBase = 'classDef base fill:#eef2ff,stroke:#6366f1,stroke-width:1px,color:#111;'
    const classDefRun = 'classDef running fill:#dbeafe,stroke:#2563eb,stroke-width:2px;'
    const classDefDone = 'classDef done fill:#dcfce7,stroke:#16a34a,stroke-width:2px;'
    const classDefFail = 'classDef fail fill:#fee2e2,stroke:#dc2626,stroke-width:2px;'
    const classDefWait = 'classDef wait fill:#fff7ed,stroke:#f59e0b,stroke-width:2px;'

    const rolesMap: Record<string, string> = {
      'Dev': 'Dev', 'Gate': 'Gate', 'QA': 'QA', 'Scribe': 'Scribe', 'Apply': 'Apply'
    }
    const classes: string[] = []
    for (const [role, node] of Object.entries(rolesMap)) {
      const st = String(roleStatus[role] || '').toUpperCase()
      const cls = st === 'FAILED' ? 'fail' : st === 'DONE' ? 'done' : st === 'RUNNING' ? 'running' : (st === 'WAIT_BUDGET' || st === 'RETRYABLE') ? 'wait' : 'base'
      classes.push(`class ${node} ${cls};`)
    }
    // Watchdog — подсвечиваем, если есть ошибки в Dev
    const wdCls = (String(roleStatus['Dev'] || '').toUpperCase() === 'FAILED') ? 'fail' : 'base'
    classes.push(`class watchdog ${wdCls};`)

    return `graph LR\n${labels}\n${edges}\n${classDefBase}\n${classDefRun}\n${classDefDone}\n${classDefFail}\n${classDefWait}\n${classes.join('\n')}`
  }, [roleStatus])

  return (
    <div className="w-full">
      <Mermaid chart={chart} />
    </div>
  )
}

export default FeatureFlightMap

