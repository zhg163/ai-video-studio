下面直接给你一份 **企业级 MVP 接口字段级 Swagger 定义**。
我用 **OpenAPI 3.0.3 YAML** 来写，便于你直接给前后端、测试、OpenAPI Generator、Swagger UI 使用。

这份内容覆盖你前面那套 MVP 的核心接口：

* 项目
* Brief
* Script
* Storyboard
* Shot
* Asset
* Audio
* Timeline
* Render
* Task

你可以先把它作为 `openapi.yaml` 的骨架，然后再按你们实际模型网关参数补充。

---

# 一、OpenAPI 3.0.3 Swagger 定义（MVP版）

```yaml
openapi: 3.0.3
info:
  title: AI Video Studio MVP API
  version: 1.0.0
  description: |
    企业级 AI 视频制作平台 MVP 接口定义。
    包含项目管理、创意输入、脚本生成、分镜生成、素材生成、时间线与导出等核心能力。

servers:
  - url: https://api.example.com
    description: Production
  - url: http://localhost:8000
    description: Local

tags:
  - name: Projects
  - name: Brief
  - name: Scripts
  - name: Storyboard
  - name: Shots
  - name: Assets
  - name: Audio
  - name: Timeline
  - name: Render
  - name: Tasks

security:
  - bearerAuth: []

paths:
  /api/v1/projects:
    post:
      tags: [Projects]
      summary: 创建项目
      operationId: createProject
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateProjectRequest'
      responses:
        '200':
          description: 创建成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectCreateResponse'

    get:
      tags: [Projects]
      summary: 查询项目列表
      operationId: listProjects
      parameters:
        - $ref: '#/components/parameters/PageNo'
        - $ref: '#/components/parameters/PageSize'
        - name: status
          in: query
          required: false
          schema:
            $ref: '#/components/schemas/ProjectStatus'
        - name: keyword
          in: query
          required: false
          schema:
            type: string
            maxLength: 255
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectPageResponse'

  /api/v1/projects/{project_id}:
    get:
      tags: [Projects]
      summary: 查询项目详情
      operationId: getProjectDetail
      parameters:
        - $ref: '#/components/parameters/ProjectId'
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectDetailResponse'

  /api/v1/projects/{project_id}/archive:
    post:
      tags: [Projects]
      summary: 归档项目
      operationId: archiveProject
      parameters:
        - $ref: '#/components/parameters/ProjectId'
      responses:
        '200':
          description: 归档成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CommonSuccessResponse'

  /api/v1/projects/{project_id}/brief:
    post:
      tags: [Brief]
      summary: 提交 creative brief 原始输入
      operationId: createBrief
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateBriefRequest'
      responses:
        '200':
          description: 提交成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BriefCreateResponse'

  /api/v1/projects/{project_id}/brief/latest:
    get:
      tags: [Brief]
      summary: 获取最新 brief
      operationId: getLatestBrief
      parameters:
        - $ref: '#/components/parameters/ProjectId'
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BriefDetailResponse'

  /api/v1/projects/{project_id}/brief/{version_no}:
    put:
      tags: [Brief]
      summary: 手工更新 brief
      operationId: updateBrief
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/VersionNo'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateBriefRequest'
      responses:
        '200':
          description: 更新成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CommonSuccessResponse'

  /api/v1/projects/{project_id}/script/generate:
    post:
      tags: [Scripts]
      summary: 生成脚本
      operationId: generateScript
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GenerateScriptRequest'
      responses:
        '200':
          description: 已提交生成任务
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ScriptGenerateResponse'

  /api/v1/projects/{project_id}/scripts:
    get:
      tags: [Scripts]
      summary: 获取脚本版本列表
      operationId: listScripts
      parameters:
        - $ref: '#/components/parameters/ProjectId'
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ScriptListResponse'

  /api/v1/projects/{project_id}/scripts/{version_no}:
    get:
      tags: [Scripts]
      summary: 获取脚本详情
      operationId: getScriptDetail
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/VersionNo'
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ScriptDetailResponse'

    put:
      tags: [Scripts]
      summary: 更新脚本
      operationId: updateScript
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/VersionNo'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateScriptRequest'
      responses:
        '200':
          description: 更新成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CommonSuccessResponse'

  /api/v1/projects/{project_id}/storyboard/generate:
    post:
      tags: [Storyboard]
      summary: 根据脚本生成分镜
      operationId: generateStoryboard
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GenerateStoryboardRequest'
      responses:
        '200':
          description: 已提交生成任务
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StoryboardGenerateResponse'

  /api/v1/projects/{project_id}/storyboard/latest:
    get:
      tags: [Storyboard]
      summary: 获取最新 storyboard
      operationId: getLatestStoryboard
      parameters:
        - $ref: '#/components/parameters/ProjectId'
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/StoryboardDetailResponse'

  /api/v1/projects/{project_id}/storyboard/{version_no}/shots:
    post:
      tags: [Shots]
      summary: 新增 shot
      operationId: createShot
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/VersionNo'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateShotRequest'
      responses:
        '200':
          description: 新增成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ShotCreateResponse'

  /api/v1/projects/{project_id}/storyboard/{version_no}/shots/{shot_id}:
    put:
      tags: [Shots]
      summary: 修改 shot
      operationId: updateShot
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/VersionNo'
        - $ref: '#/components/parameters/ShotId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateShotRequest'
      responses:
        '200':
          description: 修改成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CommonSuccessResponse'

    delete:
      tags: [Shots]
      summary: 删除 shot
      operationId: deleteShot
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/VersionNo'
        - $ref: '#/components/parameters/ShotId'
      responses:
        '200':
          description: 删除成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CommonSuccessResponse'

  /api/v1/projects/{project_id}/shots/{shot_id}/generate-image:
    post:
      tags: [Shots]
      summary: 生成 shot 关键帧图
      operationId: generateShotImage
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/ShotId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GenerateShotImageRequest'
      responses:
        '200':
          description: 已提交生成任务
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ShotGenerateTaskResponse'

  /api/v1/projects/{project_id}/shots/{shot_id}/generate-video:
    post:
      tags: [Shots]
      summary: 生成 shot 视频
      operationId: generateShotVideo
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/ShotId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GenerateShotVideoRequest'
      responses:
        '200':
          description: 已提交生成任务
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ShotGenerateTaskResponse'

  /api/v1/projects/{project_id}/storyboard/{version_no}/generate-assets:
    post:
      tags: [Assets]
      summary: 批量生成 storyboard 素材
      operationId: generateStoryboardAssets
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/VersionNo'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GenerateStoryboardAssetsRequest'
      responses:
        '200':
          description: 已提交任务
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BatchGenerateAssetsResponse'

  /api/v1/projects/{project_id}/shots/{shot_id}/assets:
    get:
      tags: [Assets]
      summary: 获取 shot 候选素材
      operationId: listShotAssets
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/ShotId'
        - name: asset_type
          in: query
          required: false
          schema:
            $ref: '#/components/schemas/AssetType'
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ShotAssetListResponse'

  /api/v1/projects/{project_id}/shots/{shot_id}/select-asset:
    post:
      tags: [Assets]
      summary: 选中某个候选素材
      operationId: selectShotAsset
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/ShotId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SelectShotAssetRequest'
      responses:
        '200':
          description: 选中成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CommonSuccessResponse'

  /api/v1/projects/{project_id}/audio/generate-voiceover:
    post:
      tags: [Audio]
      summary: 生成配音
      operationId: generateVoiceover
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GenerateVoiceoverRequest'
      responses:
        '200':
          description: 已提交任务
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AudioGenerateResponse'

  /api/v1/projects/{project_id}/audio/generate-bgm:
    post:
      tags: [Audio]
      summary: 生成 BGM
      operationId: generateBgm
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GenerateBgmRequest'
      responses:
        '200':
          description: 已提交任务
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AudioGenerateResponse'

  /api/v1/projects/{project_id}/subtitle/generate:
    post:
      tags: [Audio]
      summary: 生成字幕
      operationId: generateSubtitle
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GenerateSubtitleRequest'
      responses:
        '200':
          description: 已提交任务
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AudioGenerateResponse'

  /api/v1/projects/{project_id}/timeline/generate:
    post:
      tags: [Timeline]
      summary: 自动生成 timeline
      operationId: generateTimeline
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GenerateTimelineRequest'
      responses:
        '200':
          description: 生成成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TimelineGenerateResponse'

  /api/v1/projects/{project_id}/timeline/latest:
    get:
      tags: [Timeline]
      summary: 获取最新 timeline
      operationId: getLatestTimeline
      parameters:
        - $ref: '#/components/parameters/ProjectId'
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TimelineDetailResponse'

  /api/v1/projects/{project_id}/timeline/{version_no}:
    put:
      tags: [Timeline]
      summary: 更新时间线
      operationId: updateTimeline
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/VersionNo'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateTimelineRequest'
      responses:
        '200':
          description: 更新成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CommonSuccessResponse'

  /api/v1/projects/{project_id}/render:
    post:
      tags: [Render]
      summary: 创建导出任务
      operationId: createRenderTask
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateRenderTaskRequest'
      responses:
        '200':
          description: 已提交导出任务
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RenderTaskCreateResponse'

  /api/v1/render-tasks/{render_task_id}:
    get:
      tags: [Render]
      summary: 查询导出任务详情
      operationId: getRenderTask
      parameters:
        - $ref: '#/components/parameters/RenderTaskId'
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RenderTaskDetailResponse'

  /api/v1/projects/{project_id}/renders:
    get:
      tags: [Render]
      summary: 获取项目导出记录
      operationId: listProjectRenders
      parameters:
        - $ref: '#/components/parameters/ProjectId'
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RenderTaskListResponse'

  /api/v1/projects/{project_id}/tasks:
    get:
      tags: [Tasks]
      summary: 获取项目任务列表
      operationId: listProjectTasks
      parameters:
        - $ref: '#/components/parameters/ProjectId'
        - $ref: '#/components/parameters/PageNo'
        - $ref: '#/components/parameters/PageSize'
        - name: task_type
          in: query
          required: false
          schema:
            $ref: '#/components/schemas/TaskType'
        - name: status
          in: query
          required: false
          schema:
            $ref: '#/components/schemas/TaskStatus'
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskPageResponse'

  /api/v1/tasks/{task_id}:
    get:
      tags: [Tasks]
      summary: 查询任务详情
      operationId: getTaskDetail
      parameters:
        - $ref: '#/components/parameters/TaskId'
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskDetailResponse'

  /api/v1/tasks/{task_id}/retry:
    post:
      tags: [Tasks]
      summary: 重试任务
      operationId: retryTask
      parameters:
        - $ref: '#/components/parameters/TaskId'
      responses:
        '200':
          description: 重试已提交
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CommonSuccessResponse'

  /api/v1/tasks/{task_id}/cancel:
    post:
      tags: [Tasks]
      summary: 取消任务
      operationId: cancelTask
      parameters:
        - $ref: '#/components/parameters/TaskId'
      responses:
        '200':
          description: 取消成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CommonSuccessResponse'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  parameters:
    ProjectId:
      name: project_id
      in: path
      required: true
      schema:
        type: integer
        format: int64
        minimum: 1

    VersionNo:
      name: version_no
      in: path
      required: true
      schema:
        type: integer
        minimum: 1

    ShotId:
      name: shot_id
      in: path
      required: true
      schema:
        type: string
        maxLength: 64

    TaskId:
      name: task_id
      in: path
      required: true
      schema:
        type: integer
        format: int64
        minimum: 1

    RenderTaskId:
      name: render_task_id
      in: path
      required: true
      schema:
        type: integer
        format: int64
        minimum: 1

    PageNo:
      name: page
      in: query
      required: false
      schema:
        type: integer
        minimum: 1
        default: 1

    PageSize:
      name: page_size
      in: query
      required: false
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20

    IdempotencyKey:
      name: Idempotency-Key
      in: header
      required: false
      schema:
        type: string
        maxLength: 128
      description: 幂等请求键，建议生成类接口都传

  schemas:
    BaseResponse:
      type: object
      required: [code, message]
      properties:
        code:
          type: integer
          description: 0 表示成功，非 0 表示失败
          example: 0
        message:
          type: string
          example: success
        request_id:
          type: string
          example: req_20260406_0001

    CommonSuccessResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                success:
                  type: boolean
                  example: true

    ProjectStatus:
      type: string
      enum:
        - draft
        - brief_ready
        - scripting
        - storyboard_ready
        - generating_assets
        - timeline_ready
        - rendering
        - completed
        - archived
        - failed
        - paused

    TaskStatus:
      type: string
      enum:
        - queued
        - running
        - success
        - failed
        - canceled

    TaskType:
      type: string
      enum:
        - brief_generate
        - script_generate
        - storyboard_generate
        - image_generate
        - video_generate
        - voiceover_generate
        - bgm_generate
        - subtitle_generate
        - timeline_generate
        - render_export

    AssetType:
      type: string
      enum:
        - image
        - video
        - audio
        - subtitle
        - cover
        - script_attachment
        - reference

    SourceType:
      type: string
      enum:
        - uploaded
        - generated
        - imported

    ShotStatus:
      type: string
      enum:
        - pending
        - image_generating
        - image_ready
        - video_generating
        - video_ready
        - approved
        - failed

    TimelineTrackType:
      type: string
      enum:
        - video
        - voiceover
        - bgm
        - subtitle

    RenderStatus:
      type: string
      enum:
        - queued
        - running
        - success
        - failed
        - canceled

    Gender:
      type: string
      enum:
        - male
        - female
        - neutral

    AspectRatio:
      type: string
      enum:
        - '16:9'
        - '9:16'
        - '1:1'
        - '4:3'
        - '21:9'

    CreateProjectRequest:
      type: object
      required:
        - project_name
      properties:
        project_name:
          type: string
          minLength: 1
          maxLength: 255
          example: AI产品宣传片
        description:
          type: string
          maxLength: 2000
          example: 面向企业客户的视频
        aspect_ratio:
          $ref: '#/components/schemas/AspectRatio'
        language:
          type: string
          maxLength: 32
          example: zh-CN
        duration_target_sec:
          type: integer
          minimum: 5
          maximum: 1800
          example: 60

    ProjectSummary:
      type: object
      required:
        - project_id
        - project_name
        - status
      properties:
        project_id:
          type: integer
          format: int64
          example: 1001
        project_name:
          type: string
          example: AI产品宣传片
        description:
          type: string
          nullable: true
        status:
          $ref: '#/components/schemas/ProjectStatus'
        aspect_ratio:
          $ref: '#/components/schemas/AspectRatio'
        language:
          type: string
          example: zh-CN
        duration_target_sec:
          type: integer
          example: 60
        latest_script_version_no:
          type: integer
          example: 1
        latest_storyboard_version_no:
          type: integer
          example: 1
        latest_timeline_version_no:
          type: integer
          example: 1
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    ProjectCreateResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                project_id:
                  type: integer
                  format: int64
                  example: 1001
                status:
                  $ref: '#/components/schemas/ProjectStatus'

    ProjectPageResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                list:
                  type: array
                  items:
                    $ref: '#/components/schemas/ProjectSummary'
                total:
                  type: integer
                  example: 26
                page:
                  type: integer
                  example: 1
                page_size:
                  type: integer
                  example: 20

    ProjectDetailResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              $ref: '#/components/schemas/ProjectSummary'

    CreateBriefRequest:
      type: object
      required:
        - input_text
      properties:
        input_text:
          type: string
          minLength: 1
          maxLength: 10000
          example: 做一个60秒的AI视频平台宣传片，风格科技感，中文旁白
        reference_asset_ids:
          type: array
          maxItems: 50
          items:
            type: integer
            format: int64
        auto_generate:
          type: boolean
          default: true

    BriefStructured:
      type: object
      properties:
        goal:
          type: string
          example: 品牌宣传
        target_audience:
          type: array
          items:
            type: string
        style:
          type: string
          example: 科技感、未来感
        language:
          type: string
          example: zh-CN
        aspect_ratio:
          $ref: '#/components/schemas/AspectRatio'
        duration_sec:
          type: integer
          example: 60
        must_include:
          type: array
          items:
            type: string
        reference_assets:
          type: array
          items:
            type: integer
            format: int64

    BriefCreateResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                brief_version_no:
                  type: integer
                  example: 1
                workflow_task_id:
                  type: integer
                  format: int64
                  example: 9001
                status:
                  $ref: '#/components/schemas/TaskStatus'

    BriefDetail:
      type: object
      properties:
        project_id:
          type: integer
          format: int64
        version_no:
          type: integer
        input_text:
          type: string
        structured_brief:
          $ref: '#/components/schemas/BriefStructured'
        created_by:
          type: integer
          format: int64
        created_at:
          type: string
          format: date-time

    BriefDetailResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              $ref: '#/components/schemas/BriefDetail'

    UpdateBriefRequest:
      type: object
      properties:
        input_text:
          type: string
          maxLength: 10000
        structured_brief:
          $ref: '#/components/schemas/BriefStructured'

    GenerateScriptRequest:
      type: object
      required:
        - brief_version_no
      properties:
        brief_version_no:
          type: integer
          minimum: 1
        tone:
          type: string
          maxLength: 64
          example: professional
        length_mode:
          type: string
          maxLength: 32
          example: 60s
        language:
          type: string
          maxLength: 32
          example: zh-CN

    ScriptGenerateResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                task_id:
                  type: integer
                  format: int64
                  example: 9101
                status:
                  $ref: '#/components/schemas/TaskStatus'

    ScriptSection:
      type: object
      required:
        - section_no
        - title
        - narration
      properties:
        section_no:
          type: integer
          minimum: 1
        title:
          type: string
          maxLength: 255
        narration:
          type: string
          maxLength: 5000
        estimated_duration_sec:
          type: integer
          minimum: 1
          maximum: 600

    ScriptDetail:
      type: object
      properties:
        project_id:
          type: integer
          format: int64
        version_no:
          type: integer
        title:
          type: string
        summary:
          type: string
        sections:
          type: array
          items:
            $ref: '#/components/schemas/ScriptSection'
        full_text:
          type: string
        created_by:
          type: integer
          format: int64
        created_at:
          type: string
          format: date-time

    ScriptListResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                list:
                  type: array
                  items:
                    type: object
                    properties:
                      version_no:
                        type: integer
                      title:
                        type: string
                      created_at:
                        type: string
                        format: date-time

    ScriptDetailResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              $ref: '#/components/schemas/ScriptDetail'

    UpdateScriptRequest:
      type: object
      properties:
        title:
          type: string
          maxLength: 255
        summary:
          type: string
          maxLength: 2000
        sections:
          type: array
          items:
            $ref: '#/components/schemas/ScriptSection'
        full_text:
          type: string
          maxLength: 50000

    GenerateStoryboardRequest:
      type: object
      required:
        - script_version_no
      properties:
        script_version_no:
          type: integer
          minimum: 1
        preferred_shot_count:
          type: integer
          minimum: 1
          maximum: 100
          example: 8
        language:
          type: string
          maxLength: 32
          example: zh-CN

    StoryboardGenerateResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                task_id:
                  type: integer
                  format: int64
                status:
                  $ref: '#/components/schemas/TaskStatus'

    ShotModelConfig:
      type: object
      properties:
        image_model:
          type: string
          maxLength: 128
          example: flux-dev
        video_model:
          type: string
          maxLength: 128
          example: kling-vX

    ShotDetail:
      type: object
      required:
        - shot_id
        - shot_no
        - duration_sec
      properties:
        shot_id:
          type: string
          maxLength: 64
          example: shot_1
        shot_no:
          type: integer
          minimum: 1
        duration_sec:
          type: number
          format: float
          minimum: 0.5
          maximum: 60
          example: 4
        shot_type:
          type: string
          maxLength: 64
          example: wide
        camera_movement:
          type: string
          maxLength: 64
          example: push_in
        visual_prompt:
          type: string
          maxLength: 5000
        video_prompt:
          type: string
          maxLength: 5000
        voiceover_text:
          type: string
          maxLength: 5000
        character_refs:
          type: array
          items:
            type: string
        asset_refs:
          type: array
          items:
            type: integer
            format: int64
        model_config:
          $ref: '#/components/schemas/ShotModelConfig'
        status:
          $ref: '#/components/schemas/ShotStatus'
        selected_image_asset_id:
          type: integer
          format: int64
          nullable: true
        selected_video_asset_id:
          type: integer
          format: int64
          nullable: true
        candidate_image_asset_ids:
          type: array
          items:
            type: integer
            format: int64
        candidate_video_asset_ids:
          type: array
          items:
            type: integer
            format: int64

    SceneDetail:
      type: object
      properties:
        scene_id:
          type: string
          maxLength: 64
          example: scene_1
        scene_no:
          type: integer
          minimum: 1
        title:
          type: string
          maxLength: 255
        summary:
          type: string
          maxLength: 2000
        duration_sec:
          type: number
          format: float
        shots:
          type: array
          items:
            $ref: '#/components/schemas/ShotDetail'

    StoryboardDetail:
      type: object
      properties:
        project_id:
          type: integer
          format: int64
        version_no:
          type: integer
        scenes:
          type: array
          items:
            $ref: '#/components/schemas/SceneDetail'
        created_by:
          type: integer
          format: int64
        created_at:
          type: string
          format: date-time

    StoryboardDetailResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              $ref: '#/components/schemas/StoryboardDetail'

    CreateShotRequest:
      type: object
      required:
        - scene_id
        - shot_no
        - duration_sec
      properties:
        scene_id:
          type: string
          maxLength: 64
        shot_no:
          type: integer
          minimum: 1
        duration_sec:
          type: number
          format: float
          minimum: 0.5
          maximum: 60
        shot_type:
          type: string
          maxLength: 64
        camera_movement:
          type: string
          maxLength: 64
        visual_prompt:
          type: string
          maxLength: 5000
        video_prompt:
          type: string
          maxLength: 5000
        voiceover_text:
          type: string
          maxLength: 5000
        model_config:
          $ref: '#/components/schemas/ShotModelConfig'

    ShotCreateResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              $ref: '#/components/schemas/ShotDetail'

    UpdateShotRequest:
      type: object
      properties:
        shot_no:
          type: integer
          minimum: 1
        duration_sec:
          type: number
          format: float
          minimum: 0.5
          maximum: 60
        shot_type:
          type: string
          maxLength: 64
        camera_movement:
          type: string
          maxLength: 64
        visual_prompt:
          type: string
          maxLength: 5000
        video_prompt:
          type: string
          maxLength: 5000
        voiceover_text:
          type: string
          maxLength: 5000
        model_config:
          $ref: '#/components/schemas/ShotModelConfig'

    GenerateShotImageRequest:
      type: object
      properties:
        image_model:
          type: string
          maxLength: 128
          example: flux-dev
        candidate_count:
          type: integer
          minimum: 1
          maximum: 4
          default: 2
        resolution:
          type: string
          maxLength: 32
          example: 1024x1024
        reference_asset_ids:
          type: array
          maxItems: 10
          items:
            type: integer
            format: int64

    GenerateShotVideoRequest:
      type: object
      required:
        - input_mode
      properties:
        video_model:
          type: string
          maxLength: 128
          example: kling-vX
        input_mode:
          type: string
          enum:
            - text_to_video
            - image_to_video
            - start_end_frame_to_video
        image_asset_id:
          type: integer
          format: int64
          nullable: true
        start_frame_asset_id:
          type: integer
          format: int64
          nullable: true
        end_frame_asset_id:
          type: integer
          format: int64
          nullable: true
        duration_sec:
          type: number
          format: float
          minimum: 1
          maximum: 20
          example: 5
        resolution:
          type: string
          maxLength: 32
          example: 1280x720

    ShotGenerateTaskResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                task_id:
                  type: integer
                  format: int64
                status:
                  $ref: '#/components/schemas/TaskStatus'

    GenerateStoryboardAssetsRequest:
      type: object
      properties:
        generate_image:
          type: boolean
          default: true
        generate_video:
          type: boolean
          default: true
        generate_voiceover:
          type: boolean
          default: true
        parallel_limit:
          type: integer
          minimum: 1
          maximum: 10
          default: 3
        image_model:
          type: string
          maxLength: 128
        video_model:
          type: string
          maxLength: 128

    BatchGenerateAssetsResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                batch_task_id:
                  type: integer
                  format: int64
                status:
                  $ref: '#/components/schemas/TaskStatus'

    AssetFile:
      type: object
      properties:
        asset_id:
          type: integer
          format: int64
          example: 5001
        asset_type:
          $ref: '#/components/schemas/AssetType'
        file_name:
          type: string
        file_ext:
          type: string
        mime_type:
          type: string
        file_size:
          type: integer
          format: int64
        file_url:
          type: string
          format: uri
        width:
          type: integer
          nullable: true
        height:
          type: integer
          nullable: true
        duration_ms:
          type: integer
          format: int64
          nullable: true
        source_type:
          $ref: '#/components/schemas/SourceType'
        status:
          type: string
          example: ready
        created_at:
          type: string
          format: date-time

    ShotAssetListResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                list:
                  type: array
                  items:
                    $ref: '#/components/schemas/AssetFile'

    SelectShotAssetRequest:
      type: object
      required:
        - asset_type
        - asset_id
      properties:
        asset_type:
          type: string
          enum:
            - image
            - video
        asset_id:
          type: integer
          format: int64
          minimum: 1

    GenerateVoiceoverRequest:
      type: object
      required:
        - script_version_no
        - voice_name
      properties:
        script_version_no:
          type: integer
          minimum: 1
        voice_name:
          type: string
          maxLength: 128
          example: female_cn_01
        gender:
          $ref: '#/components/schemas/Gender'
        speed:
          type: number
          format: float
          minimum: 0.5
          maximum: 2.0
          default: 1.0
        pitch:
          type: number
          format: float
          minimum: 0.5
          maximum: 2.0
          default: 1.0

    GenerateBgmRequest:
      type: object
      required:
        - style
        - duration_sec
      properties:
        style:
          type: string
          maxLength: 255
          example: inspiring technology
        duration_sec:
          type: integer
          minimum: 5
          maximum: 1800
          example: 60

    GenerateSubtitleRequest:
      type: object
      required:
        - source_type
      properties:
        source_type:
          type: string
          enum:
            - voiceover
            - script
        source_asset_id:
          type: integer
          format: int64
          nullable: true

    AudioGenerateResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                task_id:
                  type: integer
                  format: int64
                status:
                  $ref: '#/components/schemas/TaskStatus'

    TimelineClip:
      type: object
      properties:
        clip_id:
          type: string
          maxLength: 64
        shot_id:
          type: string
          maxLength: 64
          nullable: true
        asset_id:
          type: integer
          format: int64
        start_sec:
          type: number
          format: float
        end_sec:
          type: number
          format: float
        trim_in_sec:
          type: number
          format: float
        trim_out_sec:
          type: number
          format: float
        volume:
          type: number
          format: float
          nullable: true

    SubtitleSegment:
      type: object
      properties:
        text:
          type: string
          maxLength: 500
        start_sec:
          type: number
          format: float
        end_sec:
          type: number
          format: float

    TimelineTrack:
      type: object
      properties:
        track_id:
          type: string
          maxLength: 64
        track_type:
          $ref: '#/components/schemas/TimelineTrackType'
        clips:
          type: array
          items:
            $ref: '#/components/schemas/TimelineClip'
        segments:
          type: array
          items:
            $ref: '#/components/schemas/SubtitleSegment'

    GenerateTimelineRequest:
      type: object
      required:
        - storyboard_version_no
      properties:
        storyboard_version_no:
          type: integer
          minimum: 1
        voiceover_asset_id:
          type: integer
          format: int64
          nullable: true
        bgm_asset_id:
          type: integer
          format: int64
          nullable: true
        subtitle_asset_id:
          type: integer
          format: int64
          nullable: true

    TimelineDetail:
      type: object
      properties:
        project_id:
          type: integer
          format: int64
        version_no:
          type: integer
        duration_sec:
          type: number
          format: float
        video_tracks:
          type: array
          items:
            $ref: '#/components/schemas/TimelineTrack'
        audio_tracks:
          type: array
          items:
            $ref: '#/components/schemas/TimelineTrack'
        subtitle_tracks:
          type: array
          items:
            $ref: '#/components/schemas/TimelineTrack'
        created_by:
          type: integer
          format: int64
        created_at:
          type: string
          format: date-time

    TimelineGenerateResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                timeline_version_no:
                  type: integer
                  example: 1

    TimelineDetailResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              $ref: '#/components/schemas/TimelineDetail'

    UpdateTimelineRequest:
      type: object
      required:
        - duration_sec
      properties:
        duration_sec:
          type: number
          format: float
          minimum: 0.1
        video_tracks:
          type: array
          items:
            $ref: '#/components/schemas/TimelineTrack'
        audio_tracks:
          type: array
          items:
            $ref: '#/components/schemas/TimelineTrack'
        subtitle_tracks:
          type: array
          items:
            $ref: '#/components/schemas/TimelineTrack'

    CreateRenderTaskRequest:
      type: object
      required:
        - timeline_version_no
      properties:
        timeline_version_no:
          type: integer
          minimum: 1
        resolution:
          type: string
          enum:
            - 720p
            - 1080p
            - 2k
            - 4k
          default: 1080p
        burn_subtitle:
          type: boolean
          default: true
        format:
          type: string
          enum:
            - mp4
            - mov
          default: mp4

    RenderTaskCreateResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                render_task_id:
                  type: integer
                  format: int64
                status:
                  $ref: '#/components/schemas/RenderStatus'

    RenderTask:
      type: object
      properties:
        render_task_id:
          type: integer
          format: int64
        project_id:
          type: integer
          format: int64
        timeline_version_no:
          type: integer
        render_mode:
          type: string
          example: mp4
        resolution:
          type: string
          example: 1080p
        status:
          $ref: '#/components/schemas/RenderStatus'
        progress:
          type: integer
          minimum: 0
          maximum: 100
        output_asset_id:
          type: integer
          format: int64
          nullable: true
        cover_asset_id:
          type: integer
          format: int64
          nullable: true
        output_url:
          type: string
          format: uri
          nullable: true
        error_message:
          type: string
          nullable: true
        started_at:
          type: string
          format: date-time
          nullable: true
        finished_at:
          type: string
          format: date-time
          nullable: true
        created_at:
          type: string
          format: date-time

    RenderTaskDetailResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              $ref: '#/components/schemas/RenderTask'

    RenderTaskListResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                list:
                  type: array
                  items:
                    $ref: '#/components/schemas/RenderTask'

    GenerationTask:
      type: object
      properties:
        task_id:
          type: integer
          format: int64
        project_id:
          type: integer
          format: int64
        task_type:
          $ref: '#/components/schemas/TaskType'
        biz_ref_type:
          type: string
          example: shot
        biz_ref_id:
          type: string
          example: shot_1
        model_provider:
          type: string
          example: aliyun
        model_name:
          type: string
          example: wanx-video
        status:
          $ref: '#/components/schemas/TaskStatus'
        progress:
          type: integer
          minimum: 0
          maximum: 100
        error_code:
          type: string
          nullable: true
        error_message:
          type: string
          nullable: true
        retry_count:
          type: integer
          minimum: 0
        started_at:
          type: string
          format: date-time
          nullable: true
        finished_at:
          type: string
          format: date-time
          nullable: true
        created_at:
          type: string
          format: date-time

    TaskPageResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              type: object
              properties:
                list:
                  type: array
                  items:
                    $ref: '#/components/schemas/GenerationTask'
                total:
                  type: integer
                page:
                  type: integer
                page_size:
                  type: integer

    TaskDetailResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            data:
              $ref: '#/components/schemas/GenerationTask'
```

---

# 二、这份 Swagger 的使用建议

这版已经可以直接做三件事：

## 1）给前端联调

前端可直接基于这些 schema 明确：

* 字段名
* 类型
* 必填项
* 枚举值
* 响应结构

## 2）给后端生成骨架

如果你们用 FastAPI，可以继续把它映射成：

* Pydantic request/response model
* APIRouter 路由
* OpenAPI 自动文档

## 3）给测试写用例

尤其适合做：

* 参数合法性校验
* 枚举值校验
* 必填字段校验
* 状态流转校验

---

# 三、建议你下一步补的两块

为了让这份 Swagger 真正达到交付级，建议继续补：

## 1）错误码定义

例如：

* `PROJECT_NOT_FOUND`
* `SHOT_NOT_FOUND`
* `TASK_ALREADY_RUNNING`
* `INVALID_TIMELINE_VERSION`
* `MODEL_PROVIDER_UNAVAILABLE`
* `ASSET_NOT_FOUND`
* `IDEMPOTENCY_CONFLICT`

## 2）回调/轮询规范

因为你的大量接口是异步生成型，最好统一：

* 轮询查询任务状态接口
* WebSocket/SSE 推送进度
* 完成后回写 project latest version 的规则

---

# 四、FastAPI 落地时的结构建议

你可以按下面方式拆 request/response：

```text
app/
├── api/v1/
│   ├── projects.py
│   ├── briefs.py
│   ├── scripts.py
│   ├── storyboard.py
│   ├── shots.py
│   ├── assets.py
│   ├── audio.py
│   ├── timeline.py
│   ├── render.py
│   └── tasks.py
├── schemas/
│   ├── common.py
│   ├── project.py
│   ├── brief.py
│   ├── script.py
│   ├── storyboard.py
│   ├── asset.py
│   ├── audio.py
│   ├── timeline.py
│   ├── render.py
│   └── task.py
```

---

# 五、我建议直接继续往下拆的内容

最适合下一步继续做的是这两个之一：

**A. FastAPI/Pydantic 代码骨架版 Swagger 落地**
把上面这些 schema 直接转成 Python 代码结构。

**B. 补全企业级错误码 + 响应规范 + 状态码规范**
把这份接口定义从“能看”提升到“能正式交付开发”。
