import React from 'react'
import { render, screen } from '@testing-library/react'
import { StatusPill } from '@/shadcn/ui/status-pill'

describe('StatusPill', () => {
  it('renders with default variant', () => {
    render(<StatusPill>Default</StatusPill>)
    const pill = screen.getByText('Default')
    expect(pill).toBeInTheDocument()
    expect(pill).toHaveClass('bg-blue-100')
  })

  it('renders with success variant', () => {
    render(<StatusPill variant="success">Success</StatusPill>)
    const pill = screen.getByText('Success')
    expect(pill).toBeInTheDocument()
    expect(pill).toHaveClass('bg-green-100')
  })

  it('renders with destructive variant', () => {
    render(<StatusPill variant="destructive">Error</StatusPill>)
    const pill = screen.getByText('Error')
    expect(pill).toBeInTheDocument()
    expect(pill).toHaveClass('bg-red-100')
  })

  it('renders with custom className', () => {
    render(<StatusPill className="custom-class">Custom</StatusPill>)
    const pill = screen.getByText('Custom')
    expect(pill).toBeInTheDocument()
    expect(pill).toHaveClass('custom-class')
  })
})