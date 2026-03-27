# data-access-layer

`data-access-layer` 是教师侧监督系统的持久化与检索底座，负责把结构化元数据、媒体对象、缓存状态和语义向量分别落到合适的存储介质。

它不负责页面逻辑，也不负责业务流程编排。

## 负责范围

- PostgreSQL 元数据访问
- Redis 缓存与实时状态
- MinIO / S3 媒体对象访问
- Qdrant 向量索引与语义检索

## 当前目录

```text
data-access-layer/
  src/
    data/
      postgres/
      cache/
      object_store/
      vector_store/
  tests/
  docs/
```

## 目录说明

- `src/data/postgres/`
  - 会话、事件、告警、教学卡片、导出任务等结构化数据。
- `src/data/cache/`
  - Redis 状态缓存、Pub/Sub、幂等键。
- `src/data/object_store/`
  - 原始视频、关键帧、片段、回放包、导出文件。
- `src/data/vector_store/`
  - Embedding 写入与相似案例检索。

## 仓储接口建议

- `SessionRepository`
- `EventRepository`
- `InterventionRepository`
- `MediaObjectRepository`
- `EmbeddingRepository`

## 协作约束

- 字段映射必须和 `shared-models-and-apis` 保持一致
- 具体数据库实现细节不要泄漏到 `backend-api-service`
- 语义检索与媒体对象访问都要暴露稳定的仓储接口，而不是散落工具函数

## 当前状态

目前已完成：

- 目录骨架落地
- 4 类存储边界明确

目前未完成：

- 真实仓储实现
- 迁移脚本与缓存策略
- 向量检索与对象存储适配
