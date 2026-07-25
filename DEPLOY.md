# 部署说明：把应用部署为公网 Demo

> 目标：在不暴露你本机的前提下，让任何人点开链接即可体验。
> 部署到独立云服务器（与你的电脑隔离），符合隐私边界偏好。

## 方式一（当前采用）：Render 免费部署（免找 IDE 入口）

> 适用于不想暴露本机、且 IDE 集成菜单不可用的情况。免费、公网长期可访问。

1. 把本仓库推送到 GitHub（见文末「推送到 GitHub」）。
2. 打开 [render.com](https://render.com) 免费注册并登录。
3. 点 **New + → Web Service** → 连接你的 GitHub 仓库。
4. Render 会自动读取仓库里的 `render.yaml`（已配置 `gunicorn` 启动命令与 Python 3.11）。
   - 若未识别，可手动设置：Build Command = `pip install -r requirements.txt`，Start Command = `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`，Plan = Free。
5. 点 **Create Web Service**，等待构建（首次约 1~2 分钟）。
6. 完成后获得公网地址，形如 `https://vat-calculator.onrender.com`，放入文章即可。

> 说明：免费实例空闲后会休眠，首次访问需等待几秒唤醒，属正常现象。
> `render.yaml` 优先于 `Procfile`，两者已保持一致。

## 方式二：Cloud Studio / Lighthouse 一键部署（需要 IDE 集成入口）

> 仅在你的 IDE 提供「集成」菜单时适用（当前 TRAE + CodeBuddy 环境可能不暴露该入口）。

1. 在 IDE 对话框「集成」菜单中登录 **Cloud Studio** 或 **Lighthouse**。
2. 授权后选择本仓库 `vat_calculator` 作为部署目录。
3. 平台会读取仓库中的 `Procfile` 与 `requirements.txt` 自动构建。
4. 部署完成后获得一个公网 URL（如 `https://xxx.cloudstudio.app`），放入文章即可。

> 说明：本仓库已包含 `Procfile`（`gunicorn -w 4 -b 0.0.0.0:$PORT app:app`），
> 平台注入的 `$PORT` 即为对外端口，无需改动代码。

## 方式二：自有云服务器（通用）

```bash
# 1. 上传代码到服务器后，安装依赖
pip install -r requirements.txt

# 2. 用 gunicorn 启动（生产级，替代 flask 自带的开发服务器）
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# 3.（可选）用 nginx 反代 8000 端口并配置 HTTPS 域名
```

`requirements.txt` 已包含 `gunicorn`，可直接使用。

## 方式三：容器化部署（Docker）

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

```bash
docker build -t vat-calculator .
docker run -d -p 8000:8000 vat-calculator
```

## 推送到 GitHub（Render 前置步骤）

```bash
cd vat_calculator
git init
git add .
git commit -m "增值税税负动态测算系统：含计算/对比/图表与部署配置"
# 在 GitHub 网页上新建一个空仓库（如 vat-calculator），然后：
git remote add origin https://github.com/<你的用户名>/vat-calculator.git
git branch -M main
git push -u origin main
```

推送后在 Render 连上该仓库即可（见方式一）。

> 注意：`.gitignore` 已排除 `venv/`、`__pycache__/`、`*.pyc`、`app.log`，
> 不会把本地虚拟环境和日志推上去。截图 `docs/screenshots/*.png` 会正常提交。

## 部署前检查清单

- [ ] `pytest tests/ -v` 全绿
- [ ] 确认 `app.py` 的 `debug` 在生产环境关闭（用 gunicorn 启动时不会走 `app.run`，天然关闭）
- [ ] 准备好公网 URL 后，填入 `docs/article-draft.md` 第 5 节的 Demo 链接占位
- [ ] 在文章与 README 标注「学习用途，结果仅供参考」

## 成本控制提示

- 演示用途可选用按量计费的最低配实例，空闲时可停机，避免长期费用。
- 若仅需短期展示，可部署后限时开放，结束后释放资源。
