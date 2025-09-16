```
app/
├── core/               # 全局配置、日志、权限管理
├── db/                 # 数据库连接和Base
├── models/             # ORM模型（ProjectPO, ChapterPO, Role, LinePO, VoicePO, TTSProviderPO）
├── dto/                # 数据传输对象（请求/响应验证）
├── repositories/       # 数据库增删改查封装
├── services/           # 核心业务逻辑：GPT解析、TTS生成、字幕生成
├── routers/            # FastAPI路由接口
└── main.py             # FastAPI启动入口

```