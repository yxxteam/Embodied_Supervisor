# Embodied Supervisor

`Embodied_Supervisor` 是“督教智能”项目的总览仓库，用来固化教师侧监督系统的技术边界、目录结构和协作文档。

这个仓库的定位不是“通用机器人控制平台”，也不是“普通 YOLO 检测 demo”。它对应的是一套独立于学生侧执行闭环之外的教师侧监督、纠偏和教学资产化系统，核心闭环是：

`感知 -> 判断 -> 介入 -> 沉淀`

当前目录设计同时参考了两类事实源：

- `reference/初选项目设计方案书.pdf`：给出业务闭环、云边协同和教学资产化目标。
- `yolodemo/` 当前已验证原型：给出 `todo/SOP` 驱动的视频节点切分、教师侧实时监督台雏形和离线网页回放包导出能力。

## 仓库作用

根仓库承担 4 件事：

1. 固化整体架构、模块边界和目录说明。
2. 提供跨仓协作入口，包括 README、架构图、teammate 指南和 GitHub 协作说明。
3. 约束 5 个技术边界子仓的职责，避免后续重新把功能堆回一个大仓或单脚本项目。
4. 管理阶段性交付、版本标签和跨模块依赖顺序。

## 技术分层

整个系统按 4 层理解最清楚：

1. 终端输入层：摄像头、麦克风、机器人状态和可选 Reset / Remote 信号。
2. 边缘监督层：多模态接入、时间轴对齐、SOP 状态机、偏差识别、事件上送。
3. 云端控制面：会话管理、复杂异常升级、RAG / VLM 指导生成、教学资产导出。
4. 工作站与资产层：实时监督台、时间轴回放、语义搜索、教学卡片管理。

跨这几层的所有共享对象，都必须先落到 `shared-models-and-apis`。

## 仓库地图

| 仓库 | 角色 | 当前应承接的模块 |
| --- | --- | --- |
| `edge-client-sdk` | 边缘监督执行面 | `capture-gateway`、`timeline-context`、`sop-supervisor`、`uplink-agent` |
| `backend-api-service` | 云端控制面 | `supervision-ingest-api`、`guidance-orchestrator`、`realtime-session-hub`、`asset-service` |
| `data-access-layer` | 数据持久化与检索底座 | PostgreSQL / Redis / MinIO-S3 / Qdrant 对应仓储实现 |
| `frontend-web-app` | 教师工作站 | `live-monitor-workbench`、`replay-search-studio`、`assets` 页面与 API 消费层 |
| `shared-models-and-apis` | 中央契约仓库 | OpenAPI、JSON Schema、Proto、DTO、示例请求响应、共享枚举 |

## 顶层目录

```text
Embodied_Supervisor/
  docs/
  edge-client-sdk/
  frontend-web-app/
  backend-api-service/
  data-access-layer/
  shared-models-and-apis/
```

### 目录说明

- `docs/`
  - 根仓库文档中心，放架构图、目录说明、协作说明和 teammate 使用说明。
- `edge-client-sdk/`
  - 边缘侧代码边界，负责接入、监督和上送。
- `frontend-web-app/`
  - 教师侧工作站前端，负责实时监督、回放检索和教学卡片管理界面。
- `backend-api-service/`
  - 云端控制面 API 和业务编排服务。
- `data-access-layer/`
  - 结构化元数据、媒体对象、缓存和向量检索的持久化边界。
- `shared-models-and-apis/`
  - 跨仓契约源头，任何共享字段和接口变化必须先改这里。

## 子仓内部目录约定

当前仓库已经把“文档里的结构”落成了最小目录骨架，后续代码应直接按下面的路径继续长：

```text
edge-client-sdk/src/edge/capture/
edge-client-sdk/src/edge/context/
edge-client-sdk/src/edge/supervisor/
edge-client-sdk/src/edge/uplink/

backend-api-service/src/api/ingest/
backend-api-service/src/api/guidance/
backend-api-service/src/api/realtime/
backend-api-service/src/api/assets/

data-access-layer/src/data/postgres/
data-access-layer/src/data/cache/
data-access-layer/src/data/object_store/
data-access-layer/src/data/vector_store/

frontend-web-app/src/pages/live/
frontend-web-app/src/pages/replay/
frontend-web-app/src/pages/assets/
frontend-web-app/src/lib/api/

shared-models-and-apis/openapi/
shared-models-and-apis/schemas/events/
shared-models-and-apis/schemas/entities/
shared-models-and-apis/proto/
shared-models-and-apis/examples/sop/
shared-models-and-apis/examples/http/
```

## 与 `yolodemo` 的继承关系

`yolodemo` 不是这个仓库的最终形态，但它提供了明确的原型映射：

- `schema.py -> shared-models-and-apis`
- `signals.py / signal_pipeline.py -> edge-client-sdk/src/edge/supervisor/`
- `live_monitor.py / server.py -> backend-api-service + edge-client-sdk`
- `web.py -> backend-api-service/src/api/assets/` 与 `frontend-web-app/src/pages/replay/`

后续工作应把这些原型能力拆进正式目录，而不是继续围绕 `yolodemo` 单仓堆功能。

## 开发顺序

推荐顺序不是“谁先有空谁先写”，而是按依赖关系推进：

1. 先在 `shared-models-and-apis` 明确首批 DTO、事件契约和 OpenAPI。
2. 再由 `backend-api-service` 与 `data-access-layer` 落地控制面和持久化接口。
3. 同步推进 `edge-client-sdk` 的边缘采集、监督和上送链路。
4. 最后由 `frontend-web-app` 消费稳定契约完成实时监督和回放搜索联调。

## 文档入口

- 架构图与模块 API：[docs/embodied_supervisor_module_architecture.html](docs/embodied_supervisor_module_architecture.html)
- 仓库与目录说明：[docs/仓库与目录说明.md](docs/仓库与目录说明.md)
- 原始规划说明：[docs/仓库规划说明.md](docs/仓库规划说明.md)
- GitHub 协作说明：[docs/GitHub上传与协作指南.md](docs/GitHub上传与协作指南.md)
- 机械臂参数包改动说明：[docs/机械臂返还参数包与参数接口改动说明.md](docs/机械臂返还参数包与参数接口改动说明.md)
- 队员 A 使用说明源码：[docs/teammate_a_frontend_edge_guide.tex](docs/teammate_a_frontend_edge_guide.tex)
- 队员 A 使用说明 PDF：[docs/teammate_a_frontend_edge_guide.pdf](docs/teammate_a_frontend_edge_guide.pdf)
- 队员 B 使用说明源码：[docs/teammate_b_backend_data_guide.tex](docs/teammate_b_backend_data_guide.tex)
- 队员 B 使用说明 PDF：[docs/teammate_b_backend_data_guide.pdf](docs/teammate_b_backend_data_guide.pdf)

## 当前状态

目前已经完成：

- 根仓库初始化和远端关联。
- 五个技术边界子目录建立。
- 根 README、目录说明和架构图文档完善。
- 子仓内部第一层模块骨架目录落地。
- `shared-models-and-apis` 首批 OpenAPI / Schema / Proto / 示例文件落地。

目前尚未完成：

- 边缘监督、云端控制面、工作站页面的真实实现代码。
- 自动化 CI/CD、测试基线和跨仓版本联动脚本。

## 协作约束

- 任何共享字段或接口变更，先改 `shared-models-and-apis`。
- 不允许前端、边缘端、后端各自维护不同的数据结构。
- 教师侧系统默认只做指导、告警和复位，不直接扩展成高风险运动控制栈。
- 文档里写出来的目录结构，必须与仓库实际骨架保持一致。
