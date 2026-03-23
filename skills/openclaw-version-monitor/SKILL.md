---
name: openclaw-version-monitor
description: "# OpenClaw 版本监控"
---

# OpenClaw 版本监控

## 功能

1. **检查版本** - 调用 GitHub API 获取最新版本
2. **对比版本** - 与当前版本比较，判断是否有新版本
3. **获取发布说明** - 获取完整的 changelog
4. **翻译中文** - 将英文发布说明翻译成中文
5. **推送到渠道** - 发送消息到 Telegram 和 Feishu

## 使用方法

### 检查版本

```bash
# 获取最新版本号
curl -s https://api.github.com/repos/openclaw/openclaw/releases/latest | jq -r '.tag_name'
# 返回: v2026.3.13

# 获取最新版本内容
curl -s https://api.github.com/repos/openclaw/openclaw/releases/latest | jq -r '.body'
```

### 推送格式

```
🆕 OpenClaw 版本更新 | {版本号}

📅 发布于: {日期}

━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 更新内容:

【新增功能】
• ...

【问题修复】
• ...

━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 完整更新日志:
https://github.com/openclaw/openclaw/releases/tag/{版本号}
```

### Telegram 推送

- Chat ID: 8290054457
- 限制: 4096 字符/条

### Feishu 推送

- 需要目标用户或群 ID
- 限制相对宽松

## 定时任务配置

### 工作时段 (9:00-19:00)
- 表达式: `0,30 9-18 * * *`
- 行为: 检测到新版本立即推送

### 非工作时段
- 表达式: `0 9 * * *`
- 行为: 每天早上9点检查并推送

## 当前版本

当前监控版本: 2026.3.13

## Use

Describe what the skill does and when to use it.

## Inputs

- Describe required inputs.

## Outputs

- Describe outputs and formats.

## Failure modes

- List hard blockers and expected exact error strings when applicable.

## Toolset

- `read`
- `write`
- `edit`
- `exec`

## Acceptance tests

1. **Behavioral: happy path**
   - Run: `/openclaw-version-monitor <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/openclaw-version-monitor <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  /Users/igorsilva/clawd/skills/openclaw-version-monitor/SKILL.md
```
Expected: `PASS`.

4. **No invented tools**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/check_no_invented_tools.py \
  /Users/igorsilva/clawd/skills/openclaw-version-monitor/SKILL.md
```
Expected: `PASS`.
