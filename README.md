# Go out agent

## 流式搜索

`POST /api/agent/search` 返回 `text/event-stream`。响应会在工作流节点刚开始
执行时发送进度，而不是等待整个 workflow 完成。

```bash
curl -N -X POST http://localhost:8000/api/agent/search \
  -H 'Content-Type: application/json' \
  -d '{"user_input":"查询上海天气"}'
```

事件约定：

- `node_started`：节点已经开始执行，`data.path` 标识它在嵌套 workflow 中的位置。
- `node_completed`：节点执行结束；若有异常，`data.error` 有值。
- `result`：最终业务结果。
- `error`：工作流业务错误或运行异常。
- `done`：流结束，`data.success` 表示是否得到最终结果。

这是一个 POST SSE 接口。浏览器端请用 `fetch()` 读取响应体的
`ReadableStream`；原生 `EventSource` 只支持 GET，不能直接调用此接口。
