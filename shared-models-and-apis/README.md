# shared-models-and-apis

这个仓库是多仓库协作的中心契约仓库，优先级最高。

## 建议放入

- OpenAPI 规范
- JSON Schema
- DTO 定义
- 示例请求与响应
- 跨仓库共享枚举和常量

## 初始目录

```text
schemas/
openapi/
proto/
examples/
docs/
```

## 协作约束

- 任何跨仓库字段变更先改这里
- 接口评审通过后，再推进上下游仓库适配
- 重大不兼容变更必须同步版本号和变更说明
