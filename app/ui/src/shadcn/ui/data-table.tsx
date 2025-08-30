import React from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shadcn/ui/table'
import { cn } from '@/lib/utils'

interface DataTableProps<T> {
  data: T[]
  columns: {
    key: keyof T
    title: string
    render?: (value: any, row: T) => React.ReactNode
    className?: string
  }[]
  getKey: (item: T) => string | number
  className?: string
  emptyState?: React.ReactNode
}

function DataTable<T>({ 
  data, 
  columns, 
  getKey, 
  className,
  emptyState 
}: DataTableProps<T>) {
  return (
    <div className={cn('rounded-md border', className)}>
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((column) => (
              <TableHead key={String(column.key)} className={column.className}>
                {column.title}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                {emptyState || 'Нет данных'}
              </TableCell>
            </TableRow>
          ) : (
            data.map((row) => (
              <TableRow key={getKey(row)}>
                {columns.map((column) => (
                  <TableCell key={String(column.key)} className={column.className}>
                    {column.render 
                      ? column.render(row[column.key], row)
                      : String(row[column.key])
                    }
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}

export { DataTable }