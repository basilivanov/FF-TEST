import React from 'react'
import { render, screen } from '@testing-library/react'
import { DataTable } from '@/shadcn/ui/data-table'

interface TestData {
  id: number
  name: string
  value: string
}

describe('DataTable', () => {
  const testData: TestData[] = [
    { id: 1, name: 'Item 1', value: 'Value 1' },
    { id: 2, name: 'Item 2', value: 'Value 2' },
  ]

  const columns = [
    { key: 'id', title: 'ID' },
    { key: 'name', title: 'Name' },
    { key: 'value', title: 'Value' },
  ]

  const getKey = (item: TestData) => item.id

  it('renders table with data', () => {
    render(
      <DataTable 
        data={testData} 
        columns={columns} 
        getKey={getKey} 
      />
    )

    expect(screen.getByText('ID')).toBeInTheDocument()
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Value')).toBeInTheDocument()
    
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Item 2')).toBeInTheDocument()
  })

  it('renders empty state when no data', () => {
    render(
      <DataTable 
        data={[]} 
        columns={columns} 
        getKey={getKey} 
      />
    )

    expect(screen.getByText('Нет данных')).toBeInTheDocument()
  })

  it('renders custom empty state', () => {
    render(
      <DataTable 
        data={[]} 
        columns={columns} 
        getKey={getKey} 
        emptyState={<div>Custom empty state</div>}
      />
    )

    expect(screen.getByText('Custom empty state')).toBeInTheDocument()
  })

  it('renders with custom className', () => {
    render(
      <DataTable 
        data={testData} 
        columns={columns} 
        getKey={getKey} 
        className="custom-table"
      />
    )

    const table = screen.getByRole('table')
    expect(table).toHaveClass('custom-table')
  })

  it('renders custom cell content', () => {
    const columnsWithRender = [
      { key: 'id', title: 'ID' },
      { key: 'name', title: 'Name' },
      { 
        key: 'value', 
        title: 'Value',
        render: (value: string) => <strong>{value}</strong>
      },
    ]

    render(
      <DataTable 
        data={testData} 
        columns={columnsWithRender} 
        getKey={getKey} 
      />
    )

    const strongElements = screen.getAllByRole('strong')
    expect(strongElements).toHaveLength(2)
  })
})