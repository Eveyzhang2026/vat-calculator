# 部署说明：把应用部署为公网 Demo

> 目标：在不暴露你本机的前提下，让任何人点开链接即可体验。
> 部署到独立云服务器（与你的电脑隔离），符合隐私边界偏好。
> 当前采用 **PythonAnywhere 免费版**，无需绑定信用卡。

## 已上线 Demo 地址

```
https://evey.pythonanywhere.com/
```

---

## 部署到 PythonAnywhere（免费、免信用卡）

### 1. 注册
打开 https://www.pythonanywhere.com → **Create a free account**（只需邮箱，无需绑卡）→ 登录。

### 2. 拉取代码并安装依赖
进入 **Consoles → Bash**，执行：

```bash
git clone https://github.com/Eveyzhang2026/vat-calculator.git
cd vat-calculator
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 创建 Web App
1. **Dashboard → Web** → **Add a new web app**
2. 选 **Manual configuration**
3. Python version 选 **3.11**

### 4. 配置 WSGI 文件（关键）
点开 **WSGI configuration file**（路径形如 `/var/www/用户名_pythonanywhere_com_wsgi.py`），**清空全部内容**，写入（把 `你的用户名` 换成实际用户名）：

```python
import sys
path = '/home/你的用户名/vat-calculator'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

### 5. 填写路径
在 Web 页面配置：
- **Source code**：`/home/你的用户名/vat-calculator`
- **Working directory**：会自动同步为上面的路径
- **Virtualenv**：`/home/你的用户名/vat-calculator/venv`

（Static files 与 Security 两栏**留空即可**，Flask 会自动服务 `static/`，无需设密码。）

### 6. 启动
点 **Save** → **Reload** → 等待数秒，访问：

```
https://你的用户名.pythonanywhere.com
```

---

## 部署前检查清单

- [x] `pytest tests/ -v` 全绿
- [x] 确认 `app.py` 的 `debug` 在生产环境关闭（PythonAnywhere 用 WSGI 加载 `app`，不走 `app.run`，天然关闭）
- [x] 公网 URL 已填入 `README.md` 与 `docs/article-draft.md` 第 5 节
- [x] 在文章与 README 标注「学习用途，结果仅供参考」

## 隐私边界说明

- 部署在第三方托管平台，**不会暴露本机 IP、用户名或文件**，仅运行公开代码。
- 所有数据与计算均在服务端内存完成，无数据库、无用户数据持久化。

## 其他可选平台（对比参考）

| 平台 | 信用卡要求 | 备注 |
|------|-----------|------|
| PythonAnywhere 免费版 | 不需要 | 当前采用，Flask 友好 |
| Hugging Face Spaces | 不需要 | 需加 Dockerfile，端口 7860 |
| Render | 新账号需绑卡 | 已弃用：免费实例也要绑卡 |

> 注：本仓库不再包含 Render/Heroku 专属的 `render.yaml` / `Procfile` / `runtime.txt`，部署以本文 PythonAnywhere 步骤为准。
