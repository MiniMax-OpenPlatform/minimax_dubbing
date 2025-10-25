# 阿里云 DashScope API Key 保存问题诊断

## 问题排查步骤

### 1. 检查 API Key 格式

**正确格式**: `sk-` 开头 + 字母数字组合

**示例**:
- ✅ 正确: `sk-e5f30f38eef54f6483c9a9c897da8358`
- ❌ 错误: `e5f30f38eef54f6483c9a9c897da8358` (缺少 sk- 前缀)
- ❌ 错误: `sk-abc@123` (包含特殊字符)

### 2. 查看浏览器控制台错误

1. 打开浏览器开发者工具 (按 `F12`)
2. 切换到 **Console** 标签页
3. 尝试保存 API Key
4. 查看是否有红色错误信息

**常见错误**:
- `API Key 格式应为 sk-xxx` → API Key 格式不正确
- `401 Unauthorized` → 未登录或登录过期
- `500 Internal Server Error` → 服务器错误

### 3. 检查网络请求

1. 打开浏览器开发者工具 (按 `F12`)
2. 切换到 **Network** 标签页
3. 勾选 **Preserve log**
4. 尝试保存 API Key
5. 找到 `/auth/config/` 请求，点击查看详情

**检查内容**:

**请求 (Request)**:
```json
{
  "dashscope_api_key": "sk-xxx"
}
```

**响应 (Response)** - 成功:
```json
{
  "api_endpoint": "https://api.minimaxi.com",
  "dashscope_api_key": "sk-xxx",
  "created_at": "2025-10-24T...",
  "updated_at": "2025-10-24T..."
}
```

**响应 (Response)** - 失败:
```json
{
  "detail": "错误信息",
  "error": "错误描述"
}
```

### 4. 后端测试

在服务器上运行测试脚本:

```bash
cd /data1/devin/minimax_translation
python test_config_api.py
```

**预期输出**:
```
✅ 配置 API 测试通过！
```

如果测试失败，检查：
- 数据库连接是否正常
- Django 服务是否运行
- 用户是否存在

### 5. 数据库检查

```bash
cd /data1/devin/minimax_translation
python check_config.py
```

检查输出中是否有错误信息。

## 已知问题和解决方案

### 问题 1: UserConfig 不存在

**错误信息**: `UserConfig matching query does not exist`

**原因**: 用户没有关联的配置记录

**解决方案**: 修改已应用，系统会自动创建配置记录

### 问题 2: 403 Forbidden

**错误信息**: `403 Forbidden`

**原因**: 用户未登录或认证信息过期

**解决方案**:
1. 退出登录
2. 重新登录
3. 再次尝试保存

### 问题 3: CORS 错误

**错误信息**: `CORS policy: No 'Access-Control-Allow-Origin'`

**原因**: 前后端跨域配置问题

**解决方案**:
1. 确认后端运行在 `http://localhost:5172`
2. 确认前端运行在 `http://localhost:5173`
3. 检查 Django 的 CORS 配置

### 问题 4: 表单验证失败

**错误信息**: `API Key 格式应为 sk-xxx`

**原因**: API Key 不符合格式要求

**解决方案**:
- 确保 API Key 以 `sk-` 开头
- 只包含字母和数字
- 从 [DashScope 控制台](https://dashscope.console.aliyun.com/apiKey) 复制正确的 Key

## 手动验证

### 使用 curl 测试

```bash
# 替换 YOUR_API_KEY 为你的认证 Key
# 替换 YOUR_DASHSCOPE_KEY 为要保存的 DashScope Key

curl -X PATCH http://localhost:5172/api/auth/config/ \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: YOUR_API_KEY" \
  -d '{"dashscope_api_key": "sk-test123"}'
```

**成功响应**:
```json
{
  "api_endpoint": "https://api.minimaxi.com",
  "dashscope_api_key": "sk-test123",
  ...
}
```

## 修复历史

### 2025-10-24

**问题**: `UserConfigView.get_object()` 使用了错误的方法

**修复**:
```python
# 之前 (错误)
config, created = self.request.user.config.get_or_create(...)

# 之后 (正确)
from .models import UserConfig
config, created = UserConfig.objects.get_or_create(user=self.request.user)
```

**文件**: `authentication/views.py:87-92`

## 联系支持

如果以上步骤都无法解决问题，请提供以下信息：

1. 浏览器控制台的完整错误信息 (Console 标签)
2. 网络请求的详细信息 (Network 标签 → `/auth/config/`)
3. 服务器日志 (如果有访问权限)
4. `python test_config_api.py` 的输出

---

**最后更新**: 2025-10-24
