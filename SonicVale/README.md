```
app/
├── core/               # 全局配置、tts引擎、llm引擎、ffmpeg封装、字幕生成、websocket、异步队列
├── db/                 # 数据库连接和Base
├── models/             # ORM模型
├── dto/                # 数据传输对象（请求/响应验证）
├── entity/             # 实体类（结合 ORM 与业务层）
├── repositories/       # 数据库封装
├── services/           # 核心业务逻辑
├── routers/            # FastAPI路由接口
└── main.py             # FastAPI启动入口


```
