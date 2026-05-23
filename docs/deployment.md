# 部署说明

本文档说明 TechSpar 的两种部署方式：**纯手动开发模式**和 **Docker 模式**。

> 当前你使用的是**纯手动开发模式**，推荐参考根目录的 `本地部署指南.md` 获取详细的启停、重启和状态查看命令。

---

## 快速启动（纯手动模式，当前在用）

### 环境要求

- Python `3.11+`
- Node.js `18+`
- SiliconFlow API Key（主 LLM + Embedding）

### 启动后端

```powershell
cd "C:\Users\seigi\Desktop\26面试\TechSpar"
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 启动前端

```powershell
cd "C:\Users\seigi\Desktop\26面试\TechSpar\frontend"
npm install
npm run dev
```

访问 `http://localhost:5173`

---

## Docker 启动（可选）

```powershell
cd "C:\Users\seigi\Desktop\26面试\TechSpar"
docker compose up --build
```

访问 `http://localhost`

---

## 当前 .env 配置

```env
API_BASE=https://cn.wzjself.org/v1
API_KEY=sk-live-652f527f5245cf54495a8d12d7c7f298eefa
MODEL=gpt-5.5

EMBEDDING_BACKEND=api
EMBEDDING_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_API_KEY=sk-hspbmmdlwdsafyzxwjqcwccgpbtdceuqfighoxtjhayyjuuj
EMBEDDING_API_MODEL=BAAI/bge-large-zh-v1.5
```

详细启停步骤见根目录 `本地部署指南.md`。

---

## 常见问题

**429 RateLimit（model cooldown）**：SiliconFlow gpt-5.5 配额耗尽时返回此错误，等待 18-30 分钟后自动恢复，或修改 `.env` 中 `MODEL` 为其他模型（如 `gpt-4o`）后重启后端。
