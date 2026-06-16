# 企业知识库问答系统

一个基于 Python + Vue 3 的企业级知识库问答系统，支持多格式文档上传、智能全文检索和答案高亮展示。

## ✨ 功能特性

### 文档管理
- 📄 **多格式支持**: PDF、Word (.docx)、Markdown、TXT
- 📁 **拖拽上传**: 支持点击上传和拖拽上传
- 🗑️ **文档管理**: 文档列表展示、删除操作
- 📊 **统计信息**: 文档数量、文本块数量统计

### 智能检索
- 🔍 **BM25 算法**: 基于 BM25 的全文检索，精准排序
- 🀄 **中文分词**: 集成 jieba 中文分词，支持中文关键词搜索
- 🏷️ **倒排索引**: 使用 Whoosh 构建倒排索引，快速检索
- ✨ **关键词高亮**: 自动高亮匹配的关键词，快速定位重点
- 📍 **位置信息**: 显示文本块在原文中的位置和所属章节

### 技术特点
- 📝 **文本切片**: 512 字符固定长度切片，50 字符重叠，避免语义切断
- 🎯 **章节识别**: 自动识别文档章节标题，保留结构信息
- 🔒 **单知识库**: 所有文档共享同一索引，无权限隔离
- 🎨 **精美界面**: 现代化 UI 设计，响应式布局

## 🏗️ 技术架构

### 后端技术栈
- **框架**: Flask 3.x
- **分词器**: jieba 0.42.1
- **检索引擎**: Whoosh 2.7.4 (纯 Python 实现，支持 BM25)
- **文档解析**: 
  - PyPDF2 (PDF)
  - python-docx (Word)
  - Markdown (Markdown)
- **跨域**: flask-cors
- **运行端口**: 3201

### 前端技术栈
- **框架**: Vue 3 + Composition API
- **构建工具**: Vite 5.x
- **路由**: Vue Router 4.x
- **HTTP 客户端**: Axios
- **运行端口**: 5090

## 📁 项目结构

```
dzx_248/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── __init__.py        # Flask 应用工厂
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py      # API 路由
│   │   └── core/
│   │       ├── __init__.py
│   │       ├── document_parser.py   # 文档解析器
│   │       ├── text_splitter.py     # 文本切片器
│   │       └── index_manager.py     # 索引管理器
│   ├── uploads/               # 上传文件存储目录
│   ├── index/                 # Whoosh 索引目录
│   ├── requirements.txt       # Python 依赖
│   └── run.py                 # 后端启动脚本
├── frontend/                  # 前端项目
│   ├── src/
│   │   ├── main.js           # 应用入口
│   │   ├── App.vue           # 根组件
│   │   ├── router/
│   │   │   └── index.js      # 路由配置
│   │   ├── api/
│   │   │   └── index.js      # API 封装
│   │   ├── views/
│   │   │   ├── SearchView.vue       # 搜索页面
│   │   │   └── DocumentsView.vue    # 文档管理页面
│   │   └── assets/
│   │       └── main.css       # 全局样式
│   ├── index.html            # HTML 模板
│   ├── vite.config.js        # Vite 配置
│   └── package.json          # 前端依赖
└── README.md                  # 项目说明文档
```

## 🚀 快速开始

### 环境要求
- Python >= 3.8
- Node.js >= 16.0
- npm >= 8.0 或 yarn >= 1.22

### 后端启动

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境（推荐）
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 Windows: venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 启动后端服务
```bash
python run.py
```

后端服务将在 `http://localhost:3201` 启动

### 前端启动

1. 进入前端目录（新终端）
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
# 或使用 yarn
yarn install
```

3. 启动开发服务器
```bash
npm run dev
# 或使用 yarn
yarn dev
```

前端服务将在 `http://localhost:5090` 启动

## 📖 API 接口

### 健康检查
```
GET /api/health
```

### 文档管理

#### 获取文档列表
```
GET /api/documents
```

#### 上传文档
```
POST /api/documents/upload
Content-Type: multipart/form-data

参数: file (文件)
```

#### 删除文档
```
DELETE /api/documents/:doc_id
```

### 搜索接口

#### 关键词检索
```
GET /api/search?q=关键词&top_k=3
或
POST /api/search
Content-Type: application/json

{
  "q": "关键词",
  "top_k": 3
}
```

### 统计信息
```
GET /api/stats
```

## 💡 使用说明

### 1. 上传文档
1. 访问 `http://localhost:5090`
2. 点击顶部导航栏的「📄 文档管理」
3. 点击或拖拽文件到上传区域
4. 支持格式：PDF、Word (.docx)、Markdown (.md/.markdown)、TXT
5. 点击「🚀 开始上传」按钮

### 2. 搜索问答
1. 在首页搜索框输入您的问题
2. 选择返回结果数量（1/3/5/10）
3. 按回车或点击「🔍 搜索」按钮
4. 查看搜索结果，关键词会自动高亮
5. 点击示例问题可快速搜索

### 3. 结果说明
- **相似度**: 基于 BM25 算法计算的相关度分数
- **匹配关键词**: 与查询匹配的关键词列表
- **位置**: 文本块在原文中的字符位置
- **所属文档**: 结果来自哪个文档

## 🔧 核心原理

### 文档处理流程
1. **文档解析**: 从 PDF/Word/MD/TXT 中提取纯文本，保留章节结构
2. **文本切片**: 按 512 字符切分，块间保留 50 字符重叠
3. **中文分词**: 使用 jieba 对文本块进行分词
4. **索引构建**: 使用 Whoosh 建立倒排索引，存储元数据
5. **检索排序**: 用户查询分词后，用 BM25 算法计算相似度并排序

### 文本切片策略
- 默认块大小：512 字符
- 默认重叠大小：50 字符
- 智能切分：优先在句子结束符（。！？）或段落分隔处切分
- 避免语义切断：重叠区域保证边界语义完整性

### BM25 算法
BM25 是一种基于概率检索模型的排序算法，考虑了：
- 词频（TF）：关键词在文档中出现的频率
- 逆文档频率（IDF）：关键词在整个语料库中的稀有程度
- 文档长度归一化：对长文档进行惩罚

## 🛠️ 配置说明

### 后端配置
修改 `backend/app/core/text_splitter.py` 调整切片参数：
```python
TextSplitter(chunk_size=512, chunk_overlap=50)
```

修改 `backend/app/api/routes.py` 调整默认返回结果数：
```python
top_k = int(request.args.get('top_k', 3))
```

### 前端配置
修改 `frontend/vite.config.js` 调整端口和代理：
```javascript
server: {
  port: 5090,
  proxy: {
    '/api': {
      target: 'http://localhost:3201'
    }
  }
}
```

## ❓ 常见问题

### Q: 上传 PDF 后提取的文本乱码？
A: 请确保 PDF 是可复制的文本格式，而非扫描图片。扫描版 PDF 需要先进行 OCR 识别。

### Q: 搜索不到相关结果怎么办？
A: 
1. 确认文档已成功上传并建立索引
2. 尝试使用不同的关键词
3. 检查关键词是否存在于文档中
4. 增加返回结果数量（top_k）

### Q: 支持哪些字符编码的 TXT 文件？
A: 系统默认使用 UTF-8 编码读取 TXT 文件，请确保您的文件使用 UTF-8 编码。

### Q: 索引文件存储在哪里？
A: 索引文件存储在 `backend/index/` 目录，上传的源文件存储在 `backend/uploads/` 目录。

## 📝 注意事项

- 单文件大小限制：50MB
- 目前仅支持单知识库模式，无权限隔离
- 删除文档会同时删除索引和源文件
- 建议定期备份 `backend/index/` 和 `backend/uploads/` 目录

## 🤝 技术亮点

1. **纯 Python 检索引擎**: Whoosh 无需额外服务部署，开箱即用
2. **智能中文分词**: jieba 精准分词，支持中文搜索
3. **优雅的文本切片**: 智能断点识别，避免语义切断
4. **现代化 UI 设计**: 渐变色彩、动画效果、响应式布局
5. **完整的错误处理**: 友好的错误提示，完善的异常处理

## 📄 License

MIT License
