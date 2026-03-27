# edge-client-sdk

`edge-client-sdk` 是教师侧监督系统的边缘执行面，负责把现场多模态输入组织成可监督、可上送、可复盘的结构化事件流。

它直接承接当前 `yolodemo` 原型里“视频节点切分 + 监督事件输出”的那部分能力，但会从单仓脚本形态收敛为边缘侧模块。

## 负责范围

- 摄像头、麦克风、机器人状态接入
- 多源时间戳对齐与上下文快照
- `SOP / todo` 驱动的任务节点监督
- 偏差识别与边缘初判
- 事件上送与媒体上传
- 可选的指导 / 复位命令接收桥

## 不负责

- Web 页面
- 云端控制面 API
- 数据库与对象存储实现
- 自行定义跨仓共享 DTO

## 当前目录

```text
edge-client-sdk/
  src/
    edge/
      capture/
      context/
      supervisor/
      uplink/
  tests/
  docs/
```

## 目录说明

- `src/edge/capture/`
  - 现场输入接入：RTSP / UVC / I2S / RobotState 流。
- `src/edge/context/`
  - 时间轴对齐、上下文快照、ring buffer、本地检索窗口。
- `src/edge/supervisor/`
  - 轻量检测、规则引擎、FSM、`todo/SOP` 节点进度与偏差识别。
- `src/edge/uplink/`
  - 事件上送、图片 / 视频上传、下行指导与复位桥。

## 对外契约

优先引用 `shared-models-and-apis` 中的对象：

- `TaskContextFrame`
- `TaskNodeProgress`
- `DeviationEvent`
- `InterventionTrigger`

## 主要接口

- 本地健康检查：`GET /local/healthz`
- 本地时间轴查询：`GET /local/sessions/{id}/timeline`
- 上行控制面：
  - `POST /api/v1/sessions`
  - `POST /api/v1/sessions/{id}/edge-events:batch`
  - `POST /api/v1/sessions/{id}/media`
- 下行命令 topic：
  - `embodied/{siteId}/{robotId}/guidance`
  - `embodied/{siteId}/{robotId}/command`

## 直接上游 / 下游

- 上游：终端输入层、学生侧机器人状态流
- 下游：`backend-api-service`、`shared-models-and-apis`

## 当前状态

目前已完成：

- 目录骨架落地
- 角色边界明确

目前未完成：

- 真实采集代码
- 边缘监督实现
- 上行代理实现
