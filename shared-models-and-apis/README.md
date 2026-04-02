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
  - `Session`、`SopPlan`、`PlanStep`、`TaskContextFrame`、`TeachingCard`、`MediaObject`、`SearchHit` 等实体。
- `proto/`
  - 边缘与机器人状态流的强类型消息。
- `examples/sop/`
  - 任务图谱 / `todo` 配置样例。
- `examples/http/`
  - 典型控制面请求与响应样例。

## 当前最值得先定义的对象

- `SopPlan`
- `PlanStep`
- `TaskContextFrame`
- `TaskNodeProgress`
- `DeviationEvent`
- `GuidanceSuggestion`
- `RobotParameterInput`
- `ArmCommandPacket`
- `TeachingCard`
- `MediaObject`
- `SearchHit`

## 首批已落地文件

- `openapi/control-plane.v1.json`
  - 覆盖 `sessions`、`edge-events:batch`、`media`、`guidance-requests`、`stream`、`interventions`、`teaching-cards`、`search`。
- `schemas/entities/*.json`
  - 首批包含 `Session`、`SopPlan`、`PlanStep`、`TaskContextFrame`、`RobotParameterInput`、`ArmCommandPacket`、`TeachingCard`、`MediaObject`、`SearchHit`。
- `schemas/events/*.json`
  - 首批包含 `TaskNodeProgress`、`DeviationEvent`、`GuidanceSuggestion`、`InterventionTrigger`。
- `proto/embodied_supervisor_contracts.proto`
  - 为边缘上送与下行指导提供强类型消息定义。
- `examples/sop/dual_arm_assembly.plan.yaml`
  - 演示稳定版 `SopPlan/PlanStep` 配置。
- `examples/http/*.json`
  - 提供 `create-session`、`edge-events-batch`、`media-registration`、`guidance-request`、`intervention`、`robot-parameter-input`、`teaching-cards-generate`、`semantic-search` 的示例请求响应。

## 协作约束

- 任何跨仓字段变更先改这里
- 不允许前后端或边缘端各自维护一份不同结构
- 不兼容变更必须同步版本号和变更说明

## 当前状态

目前已完成：

- 契约目录骨架落地
- 契约文件的目标分类明确
- 首批 OpenAPI 落地
- 首批事件 / 实体 Schema 落地
- Proto 消息定义落地
- 示例 SOP 与 HTTP 请求响应落地

目前未完成：

- 语义化版本发布与变更日志流程
- 契约自动校验 / codegen / breaking-change 检查
- 按子仓实现进度继续补充更多接口与对象
