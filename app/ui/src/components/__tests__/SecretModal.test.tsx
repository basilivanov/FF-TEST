import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import SecretModal from '@/components/SecretModal'

describe('SecretModal', () => {
  it('renders items and submits values', async () => {
    const items = [
      { key: 'OZON_API_KEY', hint: 'API key', required: true },
      { key: 'WB_API_TOKEN' }
    ]
    const onSubmit = jest.fn()
    const onClose = jest.fn()

    render(<SecretModal open={true} items={items} onSubmit={onSubmit} onClose={onClose} />)

    // inputs are present
    expect(screen.getByText('OZON_API_KEY')).toBeInTheDocument()
    expect(screen.getByText('WB_API_TOKEN')).toBeInTheDocument()

    const inputs = screen.getAllByPlaceholderText('Введите значение') as HTMLInputElement[]
    fireEvent.change(inputs[0], { target: { value: 'oz-secret' } })
    fireEvent.change(inputs[1], { target: { value: 'wb-secret' } })

    const submitBtn = screen.getByText('Отправить')
    fireEvent.click(submitBtn)

    // onSubmit is called with values map
    expect(onSubmit).toHaveBeenCalled()
  })
})

