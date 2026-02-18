# ClawManus 持续同步指南

## 添加上游仓库

```bash
cd ~/clawmanus
git remote add upstream https://github.com/openclaw/openclaw.git
```

## 同步官方更新

```bash
# 获取上游更新
git fetch upstream

# 切换到 custom 分支
git checkout custom

# 合并上游 main 到 custom
git merge upstream/main

# 解决冲突 (如果有)

# 推送到 GitHub
git push origin custom
```

## 自动同步 (GitHub Actions)

创建文件 `.github/workflows/sync.yml`:

```yaml
name: Sync from Upstream
on:
  schedule:
    - cron: '0 0 * * *'  # 每天
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: custom
          fetch-depth: 0
      
      - name: Add upstream
        run: |
          git remote add upstream https://github.com/openclaw/openclaw.git
      
      - name: Fetch upstream
        run: git fetch upstream
      
      - name: Merge upstream
        run: |
          git merge upstream/main --no-edit || echo "Conflict detected"
      
      - name: Push
        run: git push origin custom
```

---

## 版本发布

```bash
# 创建版本标签
git tag v1.0.0-clawmanus
git push origin v1.0.0-clawmanus
```

---

*最后更新: 2026-02-18*
