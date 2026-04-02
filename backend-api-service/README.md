# backend-api-service

`backend-api-service` 是教师侧监督系统的云端控制面，负责会话管理、边缘事件接入、复杂异常升级、实时状态流转发和教学资产导出入口。

它不负责直接存储细节，所有数据库、缓存、对象存储和向量检索访问都应下沉到 `data-access-layer`。

## 负责范围

- 控制面 API
- 会话创建与边缘事件接入
- 复杂异常升级与 VLM / RAG 调用编排
- 实时状态流与人工介入入口
- 教学卡片生成、导出与语义检索入口

## 当前目录

```text
backend-api-service/
  src/
    api/
      ingest/
      guidance/
      realtime/
      assets/
  tests/
  docs/
```

## 目录说明

- `src/api/ingest/`
  - `sessions` 创建、批量事件接入、媒体索引登记。
- `src/api/guidance/`
  - 复杂异常升级、RAG 检索、Prompt 组装、VLM 调用。
- `src/api/realtime/`
  - SSE 状态流、告警推送、人工介入入口。
- `src/api/assets/`
  - 教学卡片生成、回放包导出、语义检索和数据集导出。

## 对外 API

- `POST /api/v1/sessions`
- `GET /api/v1/sessions/{id}`
- `POST /api/v1/sessions/{id}/edge-events:batch`
- `POST /api/v1/sessions/{id}/media`
- `POST /api/v1/sessions/{id}/guidance-requests`
- `GET /api/v1/sessions/{id}/stream`
- `POST /api/v1/sessions/{id}/interventions`
- `POST /api/v1/sessions/{id}/robot-parameter-inputs`
- `GET /api/v1/sessions/{id}/robot-parameter-inputs/latest`
- `POST /api/v1/assets/teaching-cards:generate`
- `GET /api/v1/assets/teaching-cards`
- `POST /api/v1/search/semantic`

## 协作约束

- 所有接口字段必须先对齐 `shared-models-and-apis`
- 控制器里不落 SQL
- 媒体上传不直接写本地磁盘路径契约，应通过 `data-access-layer` 统一发放对象引用

## 直接上游 / 下游

- 上游：`edge-client-sdk`、`frontend-web-app`
- 下游：`data-access-layer`、外部云端 VLM 服务

## 当前状态

目前已完成：

- 目录骨架落地
- API 模块划分明确

目前未完成：

- 真实控制器 / 服务代码
- RAG / VLM 适配器
- SSE 与人工介入实现
