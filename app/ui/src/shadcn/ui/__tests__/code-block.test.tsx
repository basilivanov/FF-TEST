import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { CodeBlock } from '@/shadcn/ui/code-block'

describe('CodeBlock', () => {
  const code = '{"name": "test", "value": 123}'

  it('renders with code content', () => {
    render(<CodeBlock code={code} />)
    
    expect(screen.getByText('"name"')).toBeInTheDocument()
    expect(screen.getByText('"test"')).toBeInTheDocument()
    expect(screen.getByText('"value"')).toBeInTheDocument()
    expect(screen.getByText('123')).toBeInTheDocument()
  })

  it('renders with language label', () => {
    render(<CodeBlock code={code} language="json" />)
    
    expect(screen.getByText('JSON')).toBeInTheDocument()
  })

  it('renders with custom className', () => {
    render(<CodeBlock code={code} className="custom-code-block" />)
    
    const codeBlock = screen.getByRole('generic', { hidden: true })
    expect(codeBlock).toHaveClass('custom-code-block')
  })

  it('formats JSON code', () => {
    const unformattedCode = '{"name":"test","value":123}'
    render(<CodeBlock code={unformattedCode} language="json" />)
    
    // Check that the code is formatted with indentation
    expect(screen.getByText('  ')).toBeInTheDocument()
  })

  it('handles non-JSON code', () => {
    const nonJsonCode = 'const x = 1;'
    render(<CodeBlock code={nonJsonCode} language="javascript" />)
    
    expect(screen.getByText('const x = 1;')).toBeInTheDocument()
  })

  it('handles invalid JSON code', () => {
    const invalidJsonCode = '{"name": "test", "value":}'
    render(<CodeBlock code={invalidJsonCode} language="json" />)
    
    // Should render the code as-is when JSON is invalid
    expect(screen.getByText(invalidJsonCode)).toBeInTheDocument()
  })
})