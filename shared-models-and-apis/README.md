# shared-models-and-apis

`shared-models-and-apis` 是整个工作区优先级最高的中央契约仓库。它负责定义“模块之间到底传什么对象、字段和协议”，所有跨仓变更都必须先经过这里。

## 负责范围

- OpenAPI 规范
- JSON Schema
- Proto
- DTO
- 示例 SOP 配置
- 示例 HTTP 请求响应

## 当前目录

```text
shared-models-and-apis/
  openapi/
  schemas/
    events/
    entities/
  proto/
  examples/
    sop/
    http/
  docs/
```

## 目录说明

- `openapi/`
  - 控制面接口，如 `sessions`、`stream`、`assets`、`search`。
- `schemas/events/`
  - `TaskNodeProgress`、`DeviationEvent`、`GuidanceSuggestion`、`InterventionTrigger`。
- `schemas/entities/`
  - `Session`、`TeachingCard`、`MediaObject`、`SearchHit` 等实体。
- `proto/`
  - 边缘与机器人状态流的强类型消息。
- `examples/sop/`
  - 任务图谱 / `todo` 配置样例。
- `examples/http/`
  - 典型控制面请求与响应样例。

## 当前最值得先定义的对象

- `TaskContextFrame`
- `TaskNodeProgress`
- `DeviationEvent`
- `GuidanceSuggestion`
- `TeachingCard`
- `MediaObject`
- `SearchHit`

## 协作约束

- 任何跨仓字段变更先改这里
- 不允许前后端或边缘端各自维护一份不同结构
- 不兼容变更必须同步版本号和变更说明

## 当前状态

目前已完成：

- 契约目录骨架落地
- 契约文件的目标分类明确

目前未完成：

- 首批 OpenAPI
- 首批事件 / 实体 Schema
- Proto 消息定义
- 示例请求响应
