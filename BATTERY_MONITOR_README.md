# 电量检测定时器功能说明

## 功能概述

已成功添加电量检测定时器功能到 wechat_bot 项目中。该功能会定期检查定位器（detector）的电量，当电量低于30%时，自动发送提醒消息到"学霸乔宝专项配套办公室"群聊。

## 实现细节

### 1. 新增文件
- `detector/battery_loop.py` - 电量检测定时器主逻辑

### 2. 修改文件
- `detector_loop.py` - 集成电量检测定时器到现有的检测器循环系统

### 3. 主要功能
- **定时检测**: 默认每小时检查一次设备电量
- **低电量提醒**: 当电量低于30%时发送提醒
- **智能通知**: 避免重复通知，只在电量进一步降低时再次提醒
- **电量恢复跟踪**: 当设备电量恢复正常时，清除通知记录

### 4. 配置参数
- **检查间隔**: 默认3600秒（1小时），可通过 `set_interval()` 方法调整
- **低电量阈值**: 默认30%，可通过 `set_low_battery_threshold()` 方法调整
- **目标群聊**: 固定发送到"学霸乔宝专项配套办公室"群聊

## 技术实现

### 电池检测定时器类 (`BatteryLoop`)
```python
class BatteryLoop:
    def __init__(self, wxauto_client, env_file: str = ".env"):
        # 初始化参数
        self._interval = 3600  # 默认检查间隔
        self._low_battery_threshold = 30  # 低电量阈值
        self._last_notified_devices = {}  # 通知记录
    
    def process_loop(self, config_manager):
        # 主处理逻辑：获取设备电量并检查
        pass
    
    def _send_low_battery_notification(self, low_battery_devices):
        # 发送低电量通知
        pass
```

### 集成到检测器循环
在 `DetectorLoop` 类中新增：
```python
self.register_processor("battery_loop", BatteryLoop(self.wxauto_client, env_file))
logger.info("注册电量检测处理器...")
```

## 消息格式

当检测到低电量设备时，发送的消息格式如下：
```
⚠️ 低电量提醒 ⚠️

以下设备电量低于30%，请及时充电：

• 设备名称1: 电量百分比%
• 设备名称2: 电量百分比%

请及时充电以确保设备正常工作。
```

## 测试验证

已通过以下测试：
1. ✅ 基本功能测试 - 类实例化、方法调用
2. ✅ 通知发送测试 - 消息格式正确
3. ✅ 集成测试 - 与检测器循环系统正确集成
4. ✅ 导入测试 - 所有模块导入正常

## 使用说明

### 自动运行
电量检测定时器已集成到主程序中，当启动 `main_loop.py` 时会自动运行。

### 手动测试
```python
# 导入电池检测定时器
from detector.battery_loop import BatteryLoop

# 创建实例（需要 wxauto_client 和环境配置文件）
battery_monitor = BatteryLoop(wxauto_client, ".env")

# 调整参数（可选）
battery_monitor.set_interval(1800)  # 改为每30分钟检查一次
battery_monitor.set_low_battery_threshold(20)  # 改为20%阈值
```

## 注意事项

1. **环境配置**: 需要正确的 `.env` 配置文件，包含 QB_LOCATION 相关配置
2. **网络连接**: 需要网络连接来访问定位器API
3. **权限**: 需要有效的登录凭证来获取设备信息
4. **错误处理**: 代码包含完整的错误处理和日志记录

## 后续优化建议

1. **可配置化**: 将目标群聊、检查间隔等参数移到配置文件中
2. **多群聊支持**: 支持发送到多个群聊或联系人
3. **电量趋势分析**: 记录电量变化趋势，预测需要充电的时间
4. **紧急通知**: 当电量极低（如<10%）时发送紧急提醒