# 电量检测定时器功能说明

## 功能概述

已成功添加电量检测定时器功能到 wechat_bot 项目中。该功能会每天20:30检查定位器（detector）的电量，当电量低于30%时，自动发送提醒消息到"学霸乔宝专项配套办公室"群聊。

## 实现细节

### 1. 新增文件
- `detector/battery_loop.py` - 电量检测定时器主逻辑

### 2. 修改文件
- `detector_loop.py` - 集成电量检测定时器到现有的检测器循环系统
- `device/qb_location.py` - 增强 `get_power()` 方法，返回完整设备信息
- `device/__init__.py` - 改进导入逻辑，使其更健壮

### 3. 主要功能
- **定时检测**: 每天20:30检查一次设备电量
- **智能时间检查**: 确保每天只检查一次，即使程序重启
- **低电量提醒**: 当电量低于30%时发送提醒
- **避免重复通知**: 只在电量进一步降低时再次提醒
- **电量恢复跟踪**: 当设备电量恢复正常时，清除通知记录

### 4. 配置参数
- **检查时间**: 默认20:30，可通过 `set_check_time()` 方法调整
- **检查间隔**: 默认24小时，确保每天只检查一次
- **低电量阈值**: 默认30%，可通过 `set_low_battery_threshold()` 方法调整
- **目标群聊**: 固定发送到"学霸乔宝专项配套办公室"群聊

## 技术实现

### 电池检测定时器类 (`BatteryLoop`)
```python
class BatteryLoop:
    def __init__(self, wxauto_client, env_file: str = ".env"):
        # 初始化参数
        self._interval = 86400  # 默认24小时
        self._check_time = dt_time(20, 30)  # 每天20:30检查
        self._low_battery_threshold = 30  # 低电量阈值
        self._last_notified_devices = {}  # 通知记录
    
    def process_loop(self, config_manager):
        # 主处理逻辑：智能时间检查 + 获取设备电量
        pass
    
    def _send_low_battery_notification(self, low_battery_devices):
        # 发送低电量通知
        pass
    
    def set_check_time(self, hour: int, minute: int):
        # 设置每天检查的时间
        pass
```

### 集成到检测器循环
在 `DetectorLoop` 类中新增：
```python
self.register_processor("battery_loop", BatteryLoop(self.wxauto_client, env_file))
logger.info("注册电量检测处理器...")
```

### 增强的设备电量获取
修改了 `qb_location.py` 中的 `get_power()` 方法：
```python
def get_power(self):
    """获取所有设备的电量信息
    
    Returns:
        list: 设备信息列表，每个元素包含 device_id, device_name, power
    """
    # 返回完整设备信息，不再只返回电量
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

## 智能时间检查逻辑

1. **基本检查**: 如果距离上次检查超过24小时，则执行检查
2. **时间窗口检查**: 如果当前时间在20:30之后，且今天还没检查过，则执行检查
3. **避免重复**: 确保每天只检查一次，即使程序在20:30之后重启

## 测试验证

已通过以下测试：
1. ✅ 基本功能测试 - 类实例化、方法调用
2. ✅ 时间检查逻辑测试 - 智能时间判断
3. ✅ 通知发送测试 - 消息格式正确
4. ✅ 集成测试 - 与检测器循环系统正确集成
5. ✅ 导入测试 - 所有模块导入正常（处理了平台依赖）

## 使用说明

### 自动运行
电量检测定时器已集成到主程序中，当启动 `main_loop.py` 时会自动运行。

### 手动配置
```python
# 导入电池检测定时器
from detector.battery_loop import BatteryLoop

# 创建实例
battery_monitor = BatteryLoop(wxauto_client, ".env")

# 调整参数（可选）
battery_monitor.set_check_time(21, 0)  # 改为21:00检查
battery_monitor.set_low_battery_threshold(20)  # 改为20%阈值
```

## 注意事项

1. **环境配置**: 需要正确的 `.env` 配置文件，包含 QB_LOCATION 相关配置
2. **网络连接**: 需要网络连接来访问定位器API
3. **权限**: 需要有效的登录凭证来获取设备信息
4. **时区**: 检查时间基于系统时区，请确保系统时区正确
5. **错误处理**: 代码包含完整的错误处理和日志记录

## 设计优势

1. **规范访问**: 通过公共API获取设备信息，不直接访问私有方法
2. **健壮导入**: 处理平台特定模块的导入失败，不影响核心功能
3. **智能调度**: 确保每天只在指定时间检查一次，减少不必要的API调用
4. **易于维护**: 清晰的代码结构和完整的文档

## 后续优化建议

1. **可配置化**: 将目标群聊、检查时间等参数移到配置文件中
2. **多群聊支持**: 支持发送到多个群聊或联系人
3. **电量趋势分析**: 记录电量变化趋势，预测需要充电的时间
4. **紧急通知**: 当电量极低（如<10%）时发送紧急提醒
5. **测试覆盖率**: 添加更多单元测试和集成测试