export function formatDate(value?: string | number | Date): string {
  if (!value) return '—'
  const d = typeof value === 'string' || typeof value === 'number' ? new Date(value) : value
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString()
}

export function formatRelativeDate(value?: string | number | Date): string {
  if (!value) return ''
  const d = new Date(value)
  const diff = Date.now() - d.getTime()
  const abs = Math.abs(diff)
  const sign = diff >= 0 ? 'назад' : 'спустя'
  const sec = Math.round(abs / 1000)
  if (sec < 60) return `${sec} с ${sign}`
  const min = Math.round(sec / 60)
  if (min < 60) return `${min} мин ${sign}`
  const hr = Math.round(min / 60)
  if (hr < 24) return `${hr} ч ${sign}`
  const dys = Math.round(hr / 24)
  return `${dys} дн ${sign}`
}

export function formatFeatureStatus(status?: string): string {
  switch ((status || '').toUpperCase()) {
    case 'NEW': return 'Новая'
    case 'PLANNED': return 'Запланирована'
    case 'RUNNING': return 'В работе'
    case 'DONE': return 'Готово'
    case 'FAILED': return 'Ошибка'
    default: return status || '—'
  }
}

export function formatGraphRunStatus(status?: string): string {
  switch ((status || '').toUpperCase()) {
    case 'PENDING': return 'Ожидание'
    case 'RUNNING': return 'Выполняется'
    case 'DONE': return 'Завершено'
    case 'FAILED': return 'Ошибка'
    default: return status || '—'
  }
}

export function formatTaskStatus(status?: string): string {
  switch ((status || '').toUpperCase()) {
    case 'NEW': return 'Новая'
    case 'RUNNING': return 'Выполняется'
    case 'DONE': return 'Готово'
    case 'FAILED': return 'Ошибка'
    case 'WAIT_BUDGET': return 'Ожидание бюджета'
    case 'RETRYABLE': return 'Повтор'
    default: return status || '—'
  }
}

export function formatRole(role?: string): string {
  if (!role) return '—'
  const map: Record<string, string> = {
    Dev: 'Dev', Architect: 'Architect', QA: 'QA', Scribe: 'Scribe', Apply: 'Apply', Maintainer: 'Product', Gate: 'Gate'
  }
  return map[role] || role
}
