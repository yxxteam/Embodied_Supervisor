# GitHub 上传与协作指南

这份指南按“先本地建好，再上传，再多人协作”来组织。

## 一、建议先在 GitHub 上创建 5 个仓库

仓库名建议直接和本地目录一致：

1. `edge-client-sdk`
2. `frontend-web-app`
3. `backend-api-service`
4. `data-access-layer`
5. `shared-models-and-apis`

如果你们是一个小组长期协作，优先建议建一个 GitHub Organization，再把这 5 个仓库都放进去。这样权限更清晰。

## 二、把本地仓库第一次推上 GitHub

下面以 `backend-api-service` 为例，其它 4 个仓库完全一样。

先进入本地目录：

```powershell
cd Y:\YX\intel\Embodied_Supervisor\backend-api-service
```

如果 GitHub 上已经创建好了空仓库，执行：

```powershell
git remote add origin https://github.com/<你的用户名或组织名>/backend-api-service.git
git push -u origin main
```

如果你更习惯 SSH：

```powershell
git remote add origin git@github.com:<你的用户名或组织名>/backend-api-service.git
git push -u origin main
```

## 三、如何邀请队友

### 方案 A：仓库在你的个人账号下

1. 打开该 GitHub 仓库页面
2. 进入 `Settings`
3. 找到 `Collaborators` 或类似的成员管理入口
4. 邀请你的队友 GitHub 账号

### 方案 B：仓库在 Organization 下

1. 在 Organization 里创建团队，例如 `frontend`、`backend`、`core`
2. 把成员加进对应团队
3. 给不同仓库分配读写权限

如果你们是课程项目，最省事的做法通常是：

- 全员都有 5 个仓库的写权限
- `main` 开启保护
- 合并必须走 Pull Request

## 四、推荐的日常协作流程

每次开发都按下面做：

```powershell
git pull --rebase origin main
git checkout -b feature/<你的功能名>
```

开发完成后：

```powershell
git add .
git commit -m "feat: add <功能名>"
git push -u origin feature/<你的功能名>
```

然后在 GitHub 上发 Pull Request，不要直接把功能代码推到 `main`。

## 五、Pull Request 怎么分工

建议这样分：

- 负责契约的人优先改 `shared-models-and-apis`
- 做后端的人跟进 `backend-api-service` 和 `data-access-layer`
- 做前端的人跟进 `frontend-web-app`
- 做端侧或设备交互的人跟进 `edge-client-sdk`

如果一个需求跨多个仓库，顺序建议是：

1. 先改 `shared-models-and-apis`
2. 再改 `backend-api-service`
3. 最后改 `frontend-web-app` 或 `edge-client-sdk`

## 六、避免协作冲突的规则

- 不直接在 `main` 上开发
- 同一个需求先写清楚接口契约，再分别开工
- 小步提交，提交信息写明 `feat`、`fix`、`docs`、`refactor`
- 每天结束前把自己分支推到远端
- PR 至少让 1 个队友看过再合并

## 七、第一次给队友拉取仓库

队友本机执行：

```powershell
git clone https://github.com/<你的用户名或组织名>/shared-models-and-apis.git
git clone https://github.com/<你的用户名或组织名>/data-access-layer.git
git clone https://github.com/<你的用户名或组织名>/backend-api-service.git
git clone https://github.com/<你的用户名或组织名>/frontend-web-app.git
git clone https://github.com/<你的用户名或组织名>/edge-client-sdk.git
```

## 八、什么时候打标签

推荐在这些时间点打标签：

- 第一个能跑通的最小版本：`v0.1.0`
- 第一次前后端打通：`v0.2.0`
- 第一次对外演示：`v1.0.0-beta.1`
- 课程最终提交版：`v1.0.0`

命令示例：

```powershell
git checkout main
git pull origin main
git tag v0.1.0
git push origin v0.1.0
```
