# HS Compare Exporter（HDT 插件）

将 HDT 解析的场面写入 JSON，与 `compare_hdt.py` / Power.log 解析结果对比。

## 输出路径

```
%LocalAppData%\HSCompare\hdt_state.json
```

例如：`C:\Users\你的用户名\AppData\Local\HSCompare\hdt_state.json`

## 编译步骤

1. 安装 [Hearthstone Deck Tracker](https://hsreplay.net/downloads/)
2. Visual Studio 创建 **.NET Framework 4.7.2 类库** 项目
3. 添加引用（Copy Local = **False**）：
   - HDT 安装目录下的 `Hearthstone Deck Tracker.exe`
   - 同目录下的 `HearthDB.dll`
4. NuGet 安装 `Newtonsoft.Json`（若 HDT 目录已有可引用其 DLL）
5. 将 `CompareExporter.cs` 加入项目并编译
6. 复制生成的 DLL 到 HDT 插件目录，例如：
   ```
   %AppData%\HearthstoneDeckTracker\Plugins\HSCompareExporter.dll
   ```
7. 重启 HDT，在 **选项 → Tracker → Plugins** 中启用 **HS Compare Exporter**

## 与 Python 对比

```powershell
cd c:\Users\WIN10\Desktop\hs_claude\HS
python compare_hdt.py
```

或主程序带对比：

```powershell
python hdt_tracker.py --compare-hdt
```

开着 HDT 打一局，控制台会在发现差异时打印，便于逐项修复 `power_parser.py`。
