# frontend-web-app

`frontend-web-app` 是教师侧工作站前端，负责把实时监督、时间轴回放、语义搜索和教学卡片管理变成可操作界面。

它消费 `backend-api-service` 提供的控制面接口，不直接访问数据库或对象存储。

## 负责范围

- 实时监督台
- 时间轴回放与关键事件展示
- 语义搜索结果浏览
- 教学卡片与导出资产管理
- 前端 API 封装与状态管理

## 当前目录

```text
frontend-web-app/
  src/
    pages/
      live/
      replay/
      assets/
    lib/
      api/
  public/
  tests/
  docs/
```

## 目录说明

- `src/pages/live/`
  - 实时监督台，展示节点进度、告警和介入建议。
- `src/pages/replay/`
  - 时间轴回放、片段查看、语义搜索结果联动。
- `src/pages/assets/`
  - 教学卡片、导出记录和资产管理。
- `src/lib/api/`
  - 对 `sessions`、`stream`、`assets`、`search` 的统一访问层。

## 主要消费接口

- `GET /api/v1/sessions/{id}`
- `GET /api/v1/sessions/{id}/stream`
- `GET /api/v1/assets/teaching-cards`
- `POST /api/v1/search/semantic`
- `POST /api/v1/sessions/{id}/interventions`

## 协作约束

- 所有共享字段必须引用 `shared-models-and-apis`
- 页面层不直接拼接数据库概念
- 新接口必须先在契约仓库确认，再接前端

## 当前状态

目前已完成：

- 页面分区骨架落地
- 与控制面接口的边界明确

目前未完成：

- 页面实现
- API 客户端封装
- 状态流订阅与时间轴 UI
