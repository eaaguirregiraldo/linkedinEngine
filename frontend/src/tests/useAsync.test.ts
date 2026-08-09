import { act, renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { useAsync } from '../hooks/useAsync'

describe('hooks/useAsync — estado async con bloqueo de doble envío (H1.2, RNF-05)', () => {
  it('run() dispara la request; busy vuelve a false al terminar', async () => {
    let resolve!: (v: string) => void
    const fn = vi.fn(() => new Promise<string>((r) => (resolve = r)))

    const { result } = renderHook(() => useAsync<string>())
    let promise!: Promise<string | null>
    act(() => {
      promise = result.current.run(fn)
    })

    expect(fn).toHaveBeenCalledTimes(1)
    expect(result.current.busy).toBe(true)
    expect(result.current.error).toBeNull()

    await act(async () => {
      resolve('ok')
      await promise
    })

    expect(result.current.busy).toBe(false)
    expect(result.current.data).toBe('ok')
  })

  it('segundo run() mientras busy es IGNORADO: una sola request (RNF-05)', async () => {
    let resolve!: (v: string) => void
    const fn = vi.fn(() => new Promise<string>((r) => (resolve = r)))

    const { result } = renderHook(() => useAsync<string>())
    let first!: Promise<string | null>
    let second!: Promise<string | null>

    act(() => {
      first = result.current.run(fn)
    })
    act(() => {
      second = result.current.run(fn)
    })

    expect(fn).toHaveBeenCalledTimes(1)
    expect(result.current.busy).toBe(true)

    await act(async () => {
      resolve('ok')
      await first
      await second
    })

    expect(await second).toBeNull()
    expect(result.current.data).toBe('ok')
    expect(result.current.busy).toBe(false)
  })

  it('captura el error y deja busy en false', async () => {
    const fn = vi.fn(() => Promise.reject(new Error('boom')))

    const { result } = renderHook(() => useAsync<string>())
    await act(async () => {
      await result.current.run(fn)
    })

    expect(result.current.busy).toBe(false)
    expect(result.current.data).toBeNull()
    expect(result.current.error?.message).toBe('boom')
  })

  it('el error no persiste al correr de nuevo con éxito', async () => {
    const fail = vi.fn(() => Promise.reject(new Error('boom')))
    const ok = vi.fn(() => Promise.resolve('recuperado'))

    const { result } = renderHook(() => useAsync<string>())
    await act(async () => {
      await result.current.run(fail)
    })
    expect(result.current.error).not.toBeNull()

    await act(async () => {
      await result.current.run(ok)
    })
    expect(result.current.error).toBeNull()
    expect(result.current.data).toBe('recuperado')
  })
})
