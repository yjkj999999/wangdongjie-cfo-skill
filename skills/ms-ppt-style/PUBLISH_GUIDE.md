# 发布指南 - MS-PPT-Style Skill

## 📦 已生成的文件

| 文件 | 说明 |
|------|------|
| `ms-ppt-style.skill` | 打包好的 Skill 文件 (27.2 KB) |
| `publish-to-clawhub.sh` | 一键发布脚本 |
| `.github/workflows/publish.yml` | GitHub Actions 自动发布 |

---

## 🚀 发布到 ClawHub

### 方式1：网页手动上传

1. 访问 https://clawhub.ai/publish-skill
2. 登录您的账号
3. 上传文件：`ms-ppt-style.skill`
4. 填写信息：
   - **名称**: ms-ppt-style
   - **描述**: Morgan Stanley classic PPT style generator with bilingual support
   - **标签**: pptx, presentation, finance, morgan-stanley, bilingual

### 方式2：API 上传（需要 Token）

```bash
# 设置您的 ClawHub Token
export CLAWHUB_TOKEN="your_token_here"

# 运行发布脚本
./publish-to-clawhub.sh
```

---

## 🐙 发布到 GitHub

### 方式1：命令行

```bash
# 创建 Release
gh release create v1.0.0 ms-ppt-style.skill \
  --title "MS-PPT-Style v1.0.0" \
  --notes "Morgan Stanley PPT style generator"
```

### 方式2：GitHub Actions 自动发布

已配置 `.github/workflows/publish.yml`，推送 tag 时自动发布：

```bash
# 打标签并推送
git tag v1.0.0
git push origin v1.0.0
```

---

## 📋 发布信息模板

### 标题
```
MS-PPT-Style: Morgan Stanley PPT Generator
```

### 描述
```
摩根士丹利经典款PPT风格生成器

Features:
- 经典配色：摩根士丹利蓝 + 金色
- 渐变封面：极简深色背景，居中双语标题
- 全双语内容：所有页面中英对照
- 专业图表：瀑布图、玫瑰图、雷达图、散点矩阵、堆叠图
- 金融级排版：干净利落的投行报告风格

Compatible with: OpenClaw, WorkBuddy, QClaw
```

---

## ✅ 检查清单

- [ ] Skill 文件已生成 (`ms-ppt-style.skill`)
- [ ] YAML frontmatter 包含 name 和 description
- [ ] 测试文件运行正常
- [ ] 已上传到 ClawHub
- [ ] 已创建 GitHub Release
- [ ] 文档完整

---

> 创建：2026-05-07 | 版本：v1.0.0
