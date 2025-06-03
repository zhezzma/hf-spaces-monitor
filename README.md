# 🚀 Hugging Face 空间状态监控工具

一个自动化监控和维护 Hugging Face Spaces 运行状态的 Python 工具，支持自动检测、重建故障空间，并生成美观的监控报告。

## ✨ 功能特性

- **🔍 自动监控**: 定时检查指定的 Hugging Face Spaces 运行状态
- **🔧 智能修复**: 检测到空间故障时自动尝试重建
- **📊 可视化报告**: 生成美观的 HTML 监控报告，支持响应式设计
- **📈 统计分析**: 显示成功率、检查次数等关键指标
- **⚡ GitHub Actions**: 支持 GitHub Actions 自动化运行
- **📱 移动适配**: 完美支持移动端设备访问
- **💾 数据持久化**: JSON 格式存储历史监控数据

## 🎯 适用场景

- 维护多个 Hugging Face Spaces 的开发者
- 需要确保 AI 应用持续可用的团队
- 想要监控机器学习模型服务状态的用户
- 需要自动化运维 Hugging Face 部署的场景

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/hf-spaces-monitor.git
cd hf-spaces-monitor
```

### 2. 安装依赖

```bash
pip install requests pytz
```

### 3. 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
# Hugging Face Access Token (必需)
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Hugging Face 用户名 (必需)
export USERNAME="your-username"

# 要监控的空间列表，用逗号分隔 (必需)
export SPACE_LIST="space1,space2,space3"

# 全局超时时间，单位秒 (可选，默认1800)
export GLOBAL_TIMEOUT_SECONDS="1800"
```

### 4. 运行监控

```bash
python run.py
```

## ⚙️ 环境变量详解

| 变量名 | 必需 | 描述 | 示例 |
|--------|------|------|------|
| `HF_TOKEN` | ✅ | Hugging Face Access Token | `hf_xxxxxxxxxx` |
| `USERNAME` | ✅ | Hugging Face 用户名 | `john-doe` |
| `SPACE_LIST` | ✅ | 监控的空间列表（逗号分隔） | `chatbot,image-gen,translator` |
| `GLOBAL_TIMEOUT_SECONDS` | ❌ | 全局超时时间（秒） | `1800` |
| `GITHUB_REPOSITORY` | ❌ | GitHub 仓库路径 | `owner/repo-name` |

### 获取 Hugging Face Token

1. 访问 [Hugging Face Settings](https://huggingface.co/settings/tokens)
2. 点击 "New token"
3. 选择 "Write" 权限
4. 复制生成的 token

## 🤖 GitHub Actions 自动化

### 创建 GitHub Actions 工作流

在项目根目录创建 `.github/workflows/monitor.yml`：

```yaml
name: Hugging Face Spaces Monitor

on:
  schedule:
    # 每小时运行一次
    - cron: '0 * * * *'
  workflow_dispatch: # 允许手动触发

jobs:
  monitor:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install requests pytz
        
    - name: Run monitor
      env:
        HF_TOKEN: ${{ secrets.HF_TOKEN }}
        USERNAME: ${{ secrets.USERNAME }}
        SPACE_LIST: ${{ secrets.SPACE_LIST }}
        GLOBAL_TIMEOUT_SECONDS: ${{ secrets.GLOBAL_TIMEOUT_SECONDS }}
      run: python run.py
      
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: $${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./docs
```

### 配置 Secrets

在 GitHub 仓库设置中添加以下 Secrets：

1. 进入仓库 → Settings → Secrets and variables → Actions
2. 添加以下 secrets：
   - `HF_TOKEN`: 你的 Hugging Face Token
   - `USERNAME`: 你的 Hugging Face 用户名
   - `SPACE_LIST`: 空间列表（如：`app1,app2,app3`）
   - `GLOBAL_TIMEOUT_SECONDS`: 超时时间（可选）

### 启用 GitHub Pages

1. 进入仓库 → Settings → Pages
2. Source 选择 "GitHub Actions"
3. 保存设置

## 📁 项目结构

```
hf-spaces-monitor/
├── run.py              # 主程序文件
├── README.md           # 项目说明文档
├── .github/
│   └── workflows/
│       └── monitor.yml # GitHub Actions 工作流
└── docs/
    ├── index.html      # 监控报告页面
    └── data.js         # 监控数据（JSON格式）
```

## 📊 监控报告展示

监控工具会生成一个美观的 HTML 报告，包含：

- **📈 统计概览**: 总检查次数、成功率、最后更新时间
- **📋 详细日志**: 每次检查的详细结果和耗时
- **🎨 视觉化设计**: 现代化的响应式界面
- **📱 移动适配**: 完美支持手机和平板设备

### 示例截图

```
🚀 Hugging Face空间状态监控

┌─────────────┬─────────────┬─────────────┐
│ 总检查次数   │   成功率    │   最后更新   │
│     156     │    94%      │  14:32:10   │
└─────────────┴─────────────┴─────────────┘

🕒 2025-06-03 14:32:10
✅ chatbot: 1.23秒    ✅ image-gen: 2.45秒    ❌ translator: 45.67秒

🕒 2025-06-03 13:32:10
✅ chatbot: 0.89秒    ✅ image-gen: 1.67秒    ✅ translator: 2.34秒
```

## 🔧 高级配置

### 自定义检查间隔

修改 GitHub Actions 中的 cron 表达式：

```yaml
on:
  schedule:
    - cron: '0 */2 * * *'  # 每2小时运行
    - cron: '*/30 * * * *' # 每30分钟运行
    - cron: '0 9 * * *'    # 每天9点运行
```

### 调整超时设置

在环境变量中设置更长的超时时间：

```bash
export GLOBAL_TIMEOUT_SECONDS="3600"  # 1小时
```

### 数据保留策略

代码默认保留最新的 50 条监控记录。如需修改，请编辑 `run.py` 中的相关代码：

```python
# 保持最新的50条记录
if len(existing_data) > 50:
    # 修改这里的数字来改变保留的记录数量
```

## 🐛 故障排除

### 常见问题

1. **Token 权限不足**
   ```
   确保 HF_TOKEN 具有 Write 权限
   ```

2. **空间名称错误**
   ```
   检查 SPACE_LIST 中的空间名称是否正确
   确保空间确实存在于你的账户下
   ```

3. **GitHub Pages 部署失败**
   ```
   确保仓库启用了 GitHub Pages
   检查 Actions 权限设置
   ```

### 调试模式

启用详细日志输出：

```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Hugging Face](https://huggingface.co/) 提供优秀的 Spaces 平台
- [GitHub Actions](https://github.com/features/actions) 提供免费的 CI/CD 服务
