import { Component, type ErrorInfo, type ReactNode } from 'react'

type Props = {
  children: ReactNode
}

type State = {
  hasError: boolean
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('page_error', { message: error.message, componentStack: errorInfo.componentStack })
  }

  render(): ReactNode {
    if (!this.state.hasError) return this.props.children
    return (
      <section className="mx-auto max-w-2xl rounded-lg border border-red-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900">Something went wrong</h1>
        <p className="mt-2 text-slate-700">Please refresh the page or try again in a moment.</p>
        <button
          className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2"
          onClick={() => this.setState({ hasError: false })}
          type="button"
        >
          Try again
        </button>
      </section>
    )
  }
}
