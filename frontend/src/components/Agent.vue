
<template>
  <div class="chat-page">
    <!-- 顶部导航 -->
    <header class="chat-header">
      <div class="header-left">
        <div class="logo">AI</div>
        <span class="app-name">AI Assistant</span>
      </div>

      <div class="header-right">
        <span class="status-dot"></span>
        <span>{{ isStreaming ? '正在思考...' : '就绪' }}</span>
      </div>
    </header>

    <!-- 聊天记录 -->
    <main ref="historyRef" class="chat-history">
      <div class="message-list">
        <div
          v-for="item in messages"
          :key="item.id"
          class="message-row"
          :class="item.role"
        >
          <div
            v-if="item.role === 'assistant'"
            class="avatar ai-avatar"
          >
            AI
          </div>

          <div class="message-content">
            <div class="message-name">
              {{ item.role === 'user' ? '我' : 'AI Assistant' }}
            </div>

            <!-- 工作流执行状态 -->
            <div
              v-if="item.role === 'assistant' && item.steps?.length"
              class="workflow-panel"
            >
              <div class="workflow-title">
                <span class="workflow-indicator"></span>
                工作流执行过程
              </div>

              <div
                v-for="(step, index) in item.steps"
                :key="index"
                class="workflow-step"
              >
                <span
                  class="step-icon"
                  :class="step.status"
                >
                  {{ step.status === 'completed' ? '✓' :
                     step.status === 'running' ? '↻' : '○' }}
                </span>

                <span>{{ step.label }}</span>

                <span class="step-status">
                  {{
                    step.status === 'completed'
                      ? '已完成'
                      : step.status === 'running'
                        ? '执行中'
                        : '等待中'
                  }}
                </span>
              </div>
            </div>

            <!-- 消息气泡 -->
            <div class="message-bubble">
              <!-- AI 回复：Markdown 渲染 -->
              <div
                v-if="item.role === 'assistant'"
                class="message-text markdown-body"
                v-html="renderMarkdown(item.content)"
              ></div>

              <!-- 用户消息：仍然显示纯文本 -->
              <div v-else class="message-text">
                {{ item.content }}
              </div>

              <span
                v-if="item.streaming"
                class="typing-cursor"
              ></span>

              <span
                v-if="item.role === 'assistant' &&
                      item.streaming &&
                      !item.content &&
                      !item.steps?.some(s => s.status === 'running')"
                class="thinking-text"
              >
                正在思考...
              </span>
            </div>
          </div>

          <div
            v-if="item.role === 'user'"
            class="avatar user-avatar"
          >
            我
          </div>
        </div>
      </div>
    </main>

    <!-- 底部输入区域 -->
    <footer class="chat-footer">
      <div class="input-wrapper">
        <el-input
          v-model="inputText"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 5 }"
          resize="none"
          placeholder="输入你的问题，按 Enter 发送..."
          :disabled="isStreaming"
          @keydown.enter.exact.prevent="sendMessage"
        />

        <el-button
          class="send-button"
          type="primary"
          :disabled="!inputText.trim() || isStreaming"
          @click="sendMessage"
        >
          <el-icon :size="20">
            <Promotion />
          </el-icon>
        </el-button>
      </div>

      <div class="input-hint">
        Enter 发送 · Shift + Enter 换行
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'
import { streamChat } from '../api/chat'
import type { ChatEvent } from '../api/chat'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

type Role = 'user' | 'assistant'
type StepStatus = 'pending' | 'running' | 'completed' | 'failed'

interface WorkflowStep {
  node: string
  label: string
  status: StepStatus
}

interface Message {
  id: number
  role: Role
  content: string
  streaming?: boolean
  steps?: WorkflowStep[]
}

const inputText = ref('')
const isStreaming = ref(false)
const historyRef = ref<HTMLElement | null>(null)

let messageId = 1
let abortController: AbortController | null = null

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

function renderMarkdown(content: string) {
  return DOMPurify.sanitize(
    md.render(content),
    { USE_PROFILES: { html: true } },
  )
}

const messages = ref<Message[]>([
  {
    id: messageId++,
    role: 'assistant',
    content: '你好！我是 AI Assistant，可以告诉我你想完成什么任务。',
    steps: [],
  },
])

// 节点名称转换
const nodeLabels: Record<string, string> = {
  classify_intent: '识别用户意图',
  fallback: '处理无法识别的需求',
  plan: '制定执行计划',
  search: '搜索信息',
  extract: '提取关键信息',
  evaluate: '评估结果',
  report: '生成报告',
}

function getNodeLabel(node: string) {
  return nodeLabels[node] ?? node
}

// 自动滚动到最新消息
watch(
  messages,
  async () => {
    await nextTick()

    const el = historyRef.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  },
  { deep: true, flush: 'post' },
)

// 逐字展示结果
async function typeText(
  message: Message,
  text: string,
  signal: AbortSignal,
) {
  for (const char of text) {
    if (signal.aborted) return

    message.content += char
    await nextTick()

    await new Promise<void>((resolve) => {
      setTimeout(resolve, 15)
    })
  }
}

// 更新工作流节点状态
function updateWorkflow(
  message: Message,
  event: string,
  data: ChatEvent,
) {
  if (!data.node) return

  if (!message.steps) {
    message.steps = []
  }

  let step = message.steps.find(
    (item) => item.node === data.node,
  )

  if (!step) {
    step = {
      node: data.node,
      label: getNodeLabel(data.node),
      status: 'pending',
    }

    message.steps.push(step)
  }

  if (event === 'node_started') {
    step.status = 'running'
  } else if (event === 'node_completed') {
    step.status = 'completed'
  } else if (event === 'node_failed' || data.error) {
    step.status = 'failed'
  }
}

// 发送消息
async function sendMessage() {
  const content = inputText.value.trim()

  if (!content || isStreaming.value) return

  inputText.value = ''
  isStreaming.value = true

  const controller = new AbortController()
  abortController = controller

  // 用户消息
  messages.value.push({
    id: messageId++,
    role: 'user',
    content,
  })

  // AI 消息占位
  const rawReply: Message = {
    id: messageId++,
    role: 'assistant',
    content: '',
    streaming: true,
    steps: [],
  }

  messages.value.push(rawReply)

  const reply = messages.value[messages.value.length - 1]

  try {
    await streamChat(
      content,
      async (event, data) => {
        if (controller.signal.aborted) return

        switch (event) {
          case 'node_started':
          case 'node_completed':
          case 'node_failed':
            updateWorkflow(reply, event, data)
            break

          case 'token':
            // 如果后端以后支持逐 Token 输出
            if (typeof data.content === 'string') {
              reply.content += data.content
            }
            break

          case 'result':

            // 如果已有 Token 输出，则避免覆盖已输出内容
            if (!reply.content && typeof data.result === 'string') {
              await typeText(
                reply,
                data.result,
                controller.signal,
              )
            }
            break

          case 'error':
            reply.content =
              data.error || 'AI 处理失败，请稍后重试。'
            break

          case 'done':
            if (data.success === false && !reply.content) {
              reply.content = '任务执行失败，请重试。'
            }
            break

          default:
            console.debug('未处理的 SSE 事件:', event, data)
        }
      },
      controller.signal,
    )

    if (!reply.content && !controller.signal.aborted) {
      reply.content = '任务已结束，但没有收到结果。'
    }
  } catch (error) {
    if (!controller.signal.aborted) {
      console.error('AI 请求失败:', error)

      reply.content =
        '请求失败，请检查后端服务和网络连接。'

      ElMessage.error('AI 请求失败')
    }
  } finally {
    reply.streaming = false

    if (abortController === controller) {
      abortController = null
      isStreaming.value = false
    }
  }
}

onBeforeUnmount(() => {
  abortController?.abort()
})
</script>

<style>
* {
  box-sizing: border-box;
}

html,
body,
#app {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

body {
  font-family:
    Inter, -apple-system, BlinkMacSystemFont, "Segoe UI",
    "PingFang SC", "Microsoft YaHei", sans-serif;
}

.chat-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: #f3f8ff;
  color: #25344b;
}

/* 顶部 */
.chat-header {
  flex: 0 0 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  background: #fff;
  border-bottom: 1px solid #e8eef7;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
}

.header-left {
  gap: 12px;
}

.header-right {
  gap: 8px;
  font-size: 13px;
  color: #8190a5;
}

.logo {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: #4c8dff;
  color: white;
  font-size: 14px;
  font-weight: 700;
}

.app-name {
  font-size: 16px;
  font-weight: 600;
}

.status-dot,
.workflow-indicator {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #42c994;
}

/* 聊天历史：只有这里滚动 */
.chat-history {
  flex: 1 1 0;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 32px 24px;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 28px;
  width: 100%;
  max-width: 900px;
  min-width: 0;
  margin: 0 auto;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 36px;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.ai-avatar {
  background: #e0ebff;
  color: #3978e8;
}

.user-avatar {
  background: #c7e0ff;
  color: #2865bc;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  max-width: min(75%, 680px);
}

.message-row.user .message-content {
  align-items: flex-end;
}

.message-row.assistant .message-content {
  align-items: flex-start;
}

.message-name {
  font-size: 12px;
  color: #8b99ad;
}

.message-bubble {
  padding: 13px 17px;
  border-radius: 4px 16px 16px 16px;
  background: #fff;
  box-shadow: 0 2px 8px rgb(46 87 145 / 4%);
  font-size: 14px;
  line-height: 1.85;
  overflow-wrap: anywhere;
}

.message-row.user .message-bubble {
  border-radius: 16px 4px 16px 16px;
  background: #dcecff;
  color: #234f89;
}

.message-text {
  white-space: pre-wrap;
}

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  margin-left: 3px;
  vertical-align: text-bottom;
  background: #4c8dff;
  animation: blink 0.8s step-end infinite;
}

.thinking-text {
  color: #98a6b8;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}

/* 工作流节点状态 */
.workflow-panel {
  width: 100%;
  margin-bottom: 4px;
  padding: 12px 14px;
  border: 1px solid #e1eaf7;
  border-radius: 12px;
  background: rgb(255 255 255 / 80%);
}

.workflow-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 600;
  color: #5d6e85;
}

.workflow-indicator {
  background: #7ba8ff;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  font-size: 12px;
  color: #63748b;
}

.step-icon {
  width: 16px;
  text-align: center;
  color: #a8b5c7;
}

.step-icon.running {
  color: #4389ff;
  animation: blink 1s infinite;
}

.step-icon.completed {
  color: #31b989;
}

.step-icon.failed {
  color: #ef6262;
}

.step-status {
  margin-left: auto;
  color: #a0adbd;
}

/* 底部输入框 */
.chat-footer {
  flex: 0 0 auto;
  width: 100%;
  padding: 14px 24px calc(12px + env(safe-area-inset-bottom));
  background: #f3f8ff;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  width: 100%;
  max-width: 900px;
  min-width: 0;
  margin: 0 auto;
  padding: 12px 12px 12px 18px;
  border: 1px solid #dce6f3;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 5px 20px rgb(52 94 155 / 7%);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: #8bb7ff;
  box-shadow: 0 5px 22px rgb(52 116 220 / 10%);
}

.input-wrapper .el-textarea {
  flex: 1;
  min-width: 0;
}

.input-wrapper .el-textarea__inner {
  padding: 6px 0;
  border: none;
  box-shadow: none !important;
  background: transparent;
  color: #25344b;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.8;
}

.input-wrapper .el-textarea__inner::placeholder {
  color: #a0aec0;
}

.send-button {
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  border-radius: 13px;
}

.input-hint {
  padding-top: 9px;
  text-align: center;
  font-size: 11px;
  color: #9aa8ba;
}

@media (max-width: 600px) {
  .chat-header {
    padding: 0 16px;
  }

  .chat-history {
    padding: 20px 12px;
  }

  .message-content {
    max-width: 84%;
  }

  .chat-footer {
    padding: 10px 10px calc(8px + env(safe-area-inset-bottom));
  }
}
/* Markdown 内容 */
.markdown-body {
  min-width: 0;
  line-height: 1.8;
  overflow-wrap: anywhere;
}

.markdown-body > :first-child {
  margin-top: 0;
}

.markdown-body > :last-child {
  margin-bottom: 0;
}

.markdown-body p {
  margin: 8px 0;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  margin: 18px 0 10px;
  line-height: 1.5;
  font-weight: 600;
}

.markdown-body h1 {
  font-size: 22px;
}

.markdown-body h2 {
  font-size: 19px;
}

.markdown-body h3 {
  font-size: 16px;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 24px;
  margin: 8px 0;
}

.markdown-body li {
  margin: 4px 0;
}

.markdown-body blockquote {
  margin: 12px 0;
  padding: 4px 12px;
  border-left: 3px solid #8bb7ff;
  color: #63748b;
  background: #f5f8fd;
}

.markdown-body pre {
  max-width: 100%;
  overflow-x: auto;
  padding: 14px;
  margin: 12px 0;
  border-radius: 10px;
  background: #172033;
  color: #e6edf7;
  font-size: 13px;
  line-height: 1.6;
}

.markdown-body pre code {
  padding: 0;
  background: transparent;
  color: inherit;
}

.markdown-body :not(pre) > code {
  padding: 2px 5px;
  border-radius: 4px;
  background: #edf2fa;
  color: #d14b68;
  font-size: 0.9em;
}

.markdown-body table {
  display: block;
  max-width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
  margin: 12px 0;
}

.markdown-body th,
.markdown-body td {
  padding: 8px 12px;
  border: 1px solid #dce6f3;
  text-align: left;
}

.markdown-body th {
  background: #edf4ff;
}

.markdown-body a {
  color: #3978e8;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body hr {
  border: 0;
  border-top: 1px solid #dce6f3;
  margin: 16px 0;
}

.markdown-body img {
  max-width: 100%;
  height: auto;
}
</style>
