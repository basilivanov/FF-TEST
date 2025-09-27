import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/shadcn/ui/card'
import { Input } from '@/shadcn/ui/input'
import { Button } from '@/shadcn/ui/button'

type SecretItem = { key: string; hint?: string; required?: boolean; scope?: string }

interface Props {
  open: boolean
  items: SecretItem[]
  onClose: () => void
  onSubmit: (values: Record<string, { value: string; scope: string }>) => Promise<void> | void
}

const SecretModal: React.FC<Props> = ({ open, items, onClose, onSubmit }) => {
  const [values, setValues] = useState<Record<string, { value: string; scope: string }>>({})
  const [submitting, setSubmitting] = useState(false)

  if (!open) return null

  const setVal = (key: string, v: Partial<{ value: string; scope: string }>) => {
    setValues(prev => ({ ...prev, [key]: { value: v.value ?? prev[key]?.value ?? '', scope: v.scope ?? prev[key]?.scope ?? (items.find(i => i.key === key)?.scope || 'test') } }))
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      await onSubmit(values)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid="secret-modal">
      <Card className="w-full max-w-xl shadow-lg">
        <CardHeader>
          <CardTitle className="text-sm">Безопасная отправка секретов</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">Введите значения. Они будут сохранены в зашифрованном виде. В истории чата видны только маски.</p>
            {items.map((it) => (
              <div key={it.key} className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">{it.key} {it.required ? <span className="text-red-500">*</span> : null}</label>
                  <select
                    className="text-xs border rounded px-2 py-1"
                    defaultValue={it.scope || 'test'}
                    onChange={(e) => setVal(it.key, { scope: e.target.value })}
                  >
                    <option value="test">test</option>
                    <option value="prod">prod</option>
                  </select>
                </div>
                {it.hint ? <div className="text-xs text-muted-foreground">{it.hint}</div> : null}
                <Input
                  type="password"
                  placeholder="Введите значение"
                  onChange={(e) => setVal(it.key, { value: e.target.value })}
                />
              </div>
            ))}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={onClose} disabled={submitting}>Отмена</Button>
              <Button onClick={handleSubmit} disabled={submitting} data-testid="secret-submit">Отправить</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default SecretModal
