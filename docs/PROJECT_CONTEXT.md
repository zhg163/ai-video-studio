当前是只读模式，我不能直接写文件。下面内容可直接保存为 `docs/PROJECT_CONTEXT.md`。

```md
# PROJECT_CONTEXT

## 1. 项目概览

- 项目名称：`ai-video-studio`
- 项目定位：面向内容创作与企业生产的 AI 多智能体视频制作平台
- 当前阶段：MVP 方案设计阶段
- 核心目标：先跑通 `创意输入 -> Brief -> 脚本 -> 分镜 -> 镜头生成 -> 配音/字幕 -> 时间线 -> 导出成片` 的最小闭环

## 2. 关键文档

- `docs/产品定义.md`
  - 产品来源、功能范围、版本路线、核心模块、风险与商业化方向
- `docs/系统设计.md`
  - 第一版企业级 MVP 架构蓝图、表结构、接口设计、状态机
- `docs/系统设计2.md`
  - 第二版正式设计稿，包含：
  - MVP 模块清单
  - 服务目录结构
  - 数据库表结构 / Mongo 文档结构
  - 正式系统架构图
  - REST API 清单
  - 工作流状态机

## 3. 当前产品结论

- 这不是“单点文生视频工具”，而是“AI 视频制作生产平台”
- 产品核心不是单次生成，而是可回退、可替换、可局部重算的生产链
- 系统的三大中枢能力：
- `Project + Version` 中心
- `Workflow + Agent` 编排中枢
- `Timeline + Render` 媒体装配引擎

## 4. MVP 范围

- 必做：
- 项目创建与管理
- 创意输入与 Brief 结构化
- 脚本生成与版本管理
- Storyboard 拆分 Scene / Shot
- 单镜头关键帧生成
- 单镜头视频生成
- 配音 / 字幕生成
- Timeline 自动装配
- 成片导出
- Shot 级重生成
- 项目版本快照

- 暂不做：
- 实时多人协作
- 高级时间线特效
- 复杂审批流
- 自训练视频模型
- 模板市场与插件市场

## 5. 推荐技术架构

- 后端：`FastAPI + Pydantic v2`
- 编排：`LangGraph` 或自研状态机
- 队列：`Dramatiq` 或 `Celery`
- 数据层：`PostgreSQL + MongoDB + Redis`
- 对象存储：`MinIO`
- 媒体处理：`FFmpeg`
- 前端：`Vue 3 + TypeScript`
- 监控：`Prometheus + Grafana + Loki`

## 6. 服务拆分策略

- MVP 部署建议先用 4 个服务：
- `api-service`
- `agent-workflow-service`
- `media-render-service`
- `admin-service`

- 逻辑域按 6 类拆分：
- Project / Brief / Script
- Storyboard
- Workflow / Agent
- Asset / Media
- Timeline / Render
- Admin / Billing / Audit

## 7. 数据设计原则

- `Project` 是聚合根
- PostgreSQL 保存：
- 用户、租户、项目索引、任务元数据、审计、配额、导出记录
- MongoDB 保存：
- Brief、Script、Storyboard、Timeline、Agent 中间结果
- Redis 保存：
- 队列、缓存、锁、任务状态、幂等键
- MinIO 保存：
- 图片、视频、音频、字幕、封面、导出文件

## 8. 核心对象关系

```text
Project
├── BriefVersions
├── ScriptVersions
├── StoryboardVersions
│   ├── Scenes
│   └── Shots
├── AssetFiles
├── TimelineVersions
│   ├── Tracks
│   └── Clips
├── GenerationTasks
├── RenderTasks
└── ReviewComments
```

## 9. 状态机原则

- 项目状态：
- `draft`
- `brief_ready`
- `script_ready`
- `storyboard_ready`
- `generating`
- `editing`
- `rendering`
- `completed`
- `archived`

- Shot 状态：
- `pending`
- `image_generating`
- `image_ready`
- `video_generating`
- `audio_generating`
- `ready`
- `approved`
- `failed`

- Task 状态：
- `queued`
- `running`
- `success`
- `failed`
- `canceled`

## 10. 工作流原则

- 所有生成类操作默认异步
- 每个阶段必须支持：
- 回退
- 替换
- 局部重算
- Shot 是最小生产单元
- Timeline 是最终装配对象，不能直接用 Shot 列表替代

## 11. Agent 设计结论

- 核心 Agent：
- `CreativeAgent`
- `ScriptAgent`
- `StoryboardAgent`
- `CharacterAgent`
- `VisualAgent`
- `AudioAgent`
- `EditingAgent`
- `ReviewAgent`

- Agent 只负责：
- 结构化决策
- 工作流节点产出
- 生成策略编排

- Agent 不直接负责：
- 跨层写数据库
- 直接替代业务服务
- 绕过版本与任务系统写最终结果

## 12. 当前 OpenCode / OMO 环境结论

- OMO 当前稳定插件锁定：`oh-my-opencode@3.2.2`
- `superpowers` 已正常加载
- `sisyphus / prometheus / atlas / hephaestus / oracle` 已可被 `opencode debug agent` 正常解析
- 注意：
- 这些自定义 agent 在当前 OpenCode UI 智能体选择器中可能不显示
- 原因更可能是 OpenCode 当前版本 UI 只展示内置 `native` agent
- 这不代表 OMO agent 无效

## 13. 当前已知风险

- 角色一致性仍是视频产品核心难点
- 视频生成耗时长，必须任务化和异步化
- 模型成本高，必须做预览/高清分层和路由策略
- 输出不稳定，必须用模板化 Prompt 和结构化约束
- 合规与版权需要审核和素材来源追踪

## 14. 推荐开发顺序

1. 项目中心 + Brief
2. Script + Storyboard
3. Shot 图像/视频生成
4. TTS / 字幕
5. Timeline 自动装配
6. 成片导出
7. Shot 级重生成
8. 版本快照
9. 管理后台任务监控

## 15. 协作约定

- 优先修改已有设计文档，不重复造多个并行版本
- 设计变更优先落到：
- `docs/系统设计2.md`
- 如影响产品边界，再同步更新：
- `docs/产品定义.md`
- 如进入实现阶段，应补充：
- 服务目录结构
- DDL / Schema
- OpenAPI 请求响应样例
- 工作流节点输入输出定义

## 16. 新会话恢复上下文的顺序

重新打开项目后，优先按以下顺序恢复上下文：

1. `docs/PROJECT_CONTEXT.md`
2. `docs/产品定义.md`
3. `docs/系统设计.md`
4. `docs/系统设计2.md`
5. 再读取代码与配置，确认哪些设计已落地

## 17. 下一步建议

- 将 `系统设计2.md` 正式写入仓库
- 继续补充：
- OpenAPI 请求/响应样例
- PostgreSQL DDL 草案
- Mongo 文档 Schema 草案
- 工作流节点输入输出契约
- 前后端接口字段字典
```

如果你愿意，我下一步可以继续给你一版更“工程化”的 `PROJECT_CONTEXT.md`，加上：
1. 里程碑进度
2. 决策记录区
3. 待办区
4. 风险跟踪区