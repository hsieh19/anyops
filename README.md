# Anyops Lite 🚀

**Anyops Lite** 是一款专为网络工程师打造的轻量化、响应式运维管理平台。它基于 **FastAPI + HTMX + Ansible** 构建，旨在通过极简的架构实现复杂的网络设备自动化管理。

![Dashboard Preview](https://via.placeholder.com/800x400.png?text=Anyops+Lite+Dashboard+Mockup)

## ✨ 核心特性

- 📈 **实时监控仪表盘**：采用 HTMX 驱动，每 5 秒无刷新自动轮询设备健康指标。
- 🛡️ **资产与凭据中心**：支持设备台账管理与 SSH/密码凭据的高度关联，实现一键登录预备。
- 🖥️ **三体化视图**：
  - **仪表盘 (Dashboard)**：宏观指挥中心，异常设备自动上报。
  - **性能概览 (Overview)**：颗粒度的硬件负载监控。
  - **控制面 (Detail)**：单机作战面板，集成硬件遥测与日志流。
- 🤖 **Ansible 自动化引擎**：内置 Linux 容器化环境，原生支持华为、思科等主流厂商配置备份与巡检。

## 🛠️ 技术栈

- **后端**: Python 3.11, FastAPI
- **前端**: HTMX (无 JS 框架开发), Tailwind CSS, Lucide Icons
- **自动化**: Ansible, Ansible-Runner
- **部署**: Docker, GitHub Actions (CI/CD)
- **数据库**: SQLite

## 🚀 快速开始

### 1. 云端构建 (CI/CD)
本项目已集成 GitHub Actions。直接将代码 push 到 `main` 分支，GitHub 会自动编译镜像并发布至 `ghcr.io`。

### 2. 生产环境部署 (Debian/Ubuntu)
在您的服务器上创建一个目录，并保存以下 `docker-compose.yml` 内容：

```yaml
version: '3.8'
services:
  anyops-lite:
    image: ghcr.io/YOUR_GITHUB_USER/anyops:latest
    container_name: anyops_lite
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - ./anyops_data:/app/data
    environment:
      - ANSIBLE_HOST_KEY_CHECKING=False
```

运行启动命令：
```bash
docker compose up -d
```

## 📂 目录结构

- `main.py`: 应用入口与路由
- `core/`: 核心逻辑（数据库、Ansible 管理器）
- `templates/`: HTMX 前端模板
- `ansible/`: Ansible Playbooks 与配置文件
- `.github/`: CI/CD 自动化流水线

---
**Anyops Lite** - 让复杂的网络管理回归简单。
