# backend-api-service

这个仓库负责对外 API 和核心业务逻辑。

## 建议放入

- 路由、控制器、服务层
- 权限与鉴权
- 业务规则校验
- 对 `data-access-layer` 的编排调用

## 初始目录

```text
src/
tests/
docs/
```

## 协作约束

- API 变更先更新 `shared-models-and-apis`
- 不把 SQL 或数据库连接细节散落到控制器里
- 与前端联调前先固定请求和响应格式
