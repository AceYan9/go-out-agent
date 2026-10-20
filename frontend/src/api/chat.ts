import request from '../utils/request'

export interface ChatRequest {
  user_input: string
}

export interface ChatResponse {
  node?: string
  result?: string
  error?: string
  success?: boolean
}

export function sendChat(data: ChatRequest) {
  return request.post<ChatResponse, ChatResponse>(
    '/api/v1/agent/search',
    data,
  )
}

export interface ChatEvent {
  node?: string
  path?: string[]
  error?: string | null
  result?: string
  success?: boolean
  content?: string
}

export async function streamChat(
  user_input: string,
  onEvent: (event: string, data: ChatEvent) => void,
  signal?: AbortSignal,
) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

  const response = await fetch(`${baseURL}/api/v1/agent/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ user_input }),
    signal,
  })

  if (!response.ok) {
    throw new Error(`请求失败：HTTP ${response.status}`)
  }

  if (!response.body) {
    throw new Error('响应体为空，无法读取 SSE 流')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  let buffer = ''

  function parseBlock(block: string) {
    let event = 'message'
    const dataLines: string[] = []

    for (const line of block.split(/\r?\n/)) {
      if (line.startsWith('event:')) {
        event = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trimStart())
      }
    }

    if (!dataLines.length) return

    const raw = dataLines.join('\n')

    try {
      onEvent(event, JSON.parse(raw))
    } catch (error) {
      if (error instanceof SyntaxError) {
        onEvent(event, { content: raw })
      } else {
        throw error
      }
    }
  }

  try {
    while (true) {
      const { value, done } = await reader.read()

      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const blocks = buffer.split(/\r?\n\r?\n/)
      buffer = blocks.pop() ?? ''

      for (const block of blocks) {
        if (block.trim()) {
          parseBlock(block)
        }
      }
    }

    buffer += decoder.decode()

    if (buffer.trim()) {
      parseBlock(buffer)
    }
  } finally {
    reader.releaseLock()
  }
}
