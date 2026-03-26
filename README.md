# Embodied Supervisor Workspace

这个目录是基于 `Y:\YX\intel\reference\模块化与敏捷并行：面向Vibe Coding的全栈项目多仓库架构设计.pdf` 搭建的本地多仓库工作区。

它不是“把所有内容一起上传”的单仓库，而是一个本地工作台。默认做法是分别把下面 5 个子目录初始化并上传为 5 个 GitHub 仓库：

1. `edge-client-sdk`
2. `frontend-web-app`
3. `backend-api-service`
4. `data-access-layer`
5. `shared-models-and-apis`

## 推荐依赖关系

```text
shared-models-and-apis
        |         \
        |          \
backend-api-service  frontend-web-app
        |
data-access-layer
        |
edge-client-sdk
```

更准确地说：

- `shared-models-and-apis` 提供跨仓库契约，是最先稳定下来的仓库。
- `backend-api-service` 消费共享模型，并调用 `data-access-layer`。
- `frontend-web-app` 消费共享接口定义和后端 API。
- `edge-client-sdk` 负责设备侧或客户端底层能力，与云端交互协议保持一致。

## 当前工作区结构

```text
Embodied_Supervisor/
  docs/
  edge-client-sdk/
  frontend-web-app/
  backend-api-service/
  data-access-layer/
  shared-models-and-apis/
```

## 建议启动顺序

1. 先完善 `shared-models-and-apis` 的数据模型与接口契约。
2. 再推进 `backend-api-service` 和 `data-access-layer`。
3. 最后并行推进 `frontend-web-app` 与 `edge-client-sdk`。

具体上传 GitHub 和多人协作方式见 [docs/GitHub上传与协作指南.md](docs/GitHub上传与协作指南.md)。
