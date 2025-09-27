import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { Sparkline } from '@/components/Sparkline'

describe('Sparkline', () => {
  const mockData = [
    { value: 10, timestamp: '2024-01-01T10:00:00Z' },
    { value: 20, timestamp: '2024-01-01T10:01:00Z' },
    { value: 15, timestamp: '2024-01-01T10:02:00Z' },
    { value: 25, timestamp: '2024-01-01T10:03:00Z' },
    { value: 30, timestamp: '2024-01-01T10:04:00Z' }
  ]

  it('renders sparkline with data', () => {
    render(<Sparkline data={mockData} width={100} height={40} color="#3B82F6" />)

    const svg = screen.getByTestId('sparkline-svg')
    expect(svg).toBeInTheDocument()
    expect(svg).toHaveAttribute('width', '100')
    expect(svg).toHaveAttribute('height', '40')
  })

  it('renders path element for line', () => {
    render(<Sparkline data={mockData} width={100} height={40} color="#3B82F6" />)

    const path = screen.getByTestId('sparkline-path')
    expect(path).toBeInTheDocument()
    expect(path).toHaveAttribute('stroke', '#3B82F6')
    expect(path).toHaveAttribute('fill', 'none')
  })

  it('renders area fill when showArea is true', () => {
    render(
      <Sparkline
        data={mockData}
        width={100}
        height={40}
        color="#3B82F6"
        showArea={true}
      />
    )

    const areaPath = screen.getByTestId('sparkline-area')
    expect(areaPath).toBeInTheDocument()
  })

  it('does not render area when showArea is false', () => {
    render(
      <Sparkline
        data={mockData}
        width={100}
        height={40}
        color="#3B82F6"
        showArea={false}
      />
    )

    const areaPath = screen.queryByTestId('sparkline-area')
    expect(areaPath).not.toBeInTheDocument()
  })

  it('renders dots when showDots is true', () => {
    render(
      <Sparkline
        data={mockData}
        width={100}
        height={40}
        color="#3B82F6"
        showDots={true}
      />
    )

    const dots = screen.getAllByTestId(/sparkline-dot-/)
    expect(dots).toHaveLength(mockData.length)
  })

  it('does not render dots when showDots is false', () => {
    render(
      <Sparkline
        data={mockData}
        width={100}
        height={40}
        color="#3B82F6"
        showDots={false}
      />
    )

    const dots = screen.queryAllByTestId(/sparkline-dot-/)
    expect(dots).toHaveLength(0)
  })

  it('handles empty data array', () => {
    render(<Sparkline data={[]} width={100} height={40} color="#3B82F6" />)

    const emptyState = screen.getByTestId('sparkline-empty')
    expect(emptyState).toBeInTheDocument()
    expect(screen.getByText('Нет данных')).toBeInTheDocument()

    const svg = screen.queryByTestId('sparkline-svg')
    expect(svg).not.toBeInTheDocument()
  })

  it('handles single data point', () => {
    const singlePoint = [{ value: 10, timestamp: '2024-01-01T10:00:00Z' }]

    render(<Sparkline data={singlePoint} width={100} height={40} color="#3B82F6" />)

    const svg = screen.getByTestId('sparkline-svg')
    expect(svg).toBeInTheDocument()
  })

  it('applies custom stroke width', () => {
    render(
      <Sparkline
        data={mockData}
        width={100}
        height={40}
        color="#3B82F6"
        strokeWidth={3}
      />
    )

    const path = screen.getByTestId('sparkline-path')
    expect(path).toHaveAttribute('stroke-width', '3')
  })

  it('uses default stroke width when not specified', () => {
    render(<Sparkline data={mockData} width={100} height={40} color="#3B82F6" />)

    const path = screen.getByTestId('sparkline-path')
    expect(path).toHaveAttribute('stroke-width', '2')
  })

  it('scales data correctly to fit dimensions', () => {
    render(<Sparkline data={mockData} width={100} height={40} color="#3B82F6" />)

    const path = screen.getByTestId('sparkline-path')
    const pathData = path.getAttribute('d')

    // Path should start with M (move to) command after trimming space
    expect(pathData?.trim()).toMatch(/^M/)

    // Path should contain L (line to) commands
    expect(pathData).toMatch(/L/)
  })

  it('applies correct viewBox for responsive sizing', () => {
    render(<Sparkline data={mockData} width={100} height={40} color="#3B82F6" />)

    const svg = screen.getByTestId('sparkline-svg')
    expect(svg).toHaveAttribute('viewBox', '0 0 100 40')
  })

  it('preserves aspect ratio', () => {
    render(<Sparkline data={mockData} width={100} height={40} color="#3B82F6" />)

    const svg = screen.getByTestId('sparkline-svg')
    expect(svg).toHaveAttribute('preserveAspectRatio', 'none')
  })
})