# 鱼类和铲具百科

`data/translations/encyclopedia_fish_tools.json` 收录本地 3.89.1 `GAME.NFO` 中八个主题的正文，包含白鲑、鳊鱼、鲑鱼、狗鱼、木铲、铲、铲刃和铲柄。当前原版资源中有独立百科页的鱼种为这四种，其余鱼种在钓鱼介绍中提及，或只有物品名。

47 个正文片段沿用 [百科材料与工具条目](encyclopedia-materials.md) 的显示匹配方式。正文由 `show_topic` 读取后送给 `link_show`，词表保留原有换行标签和 40 个显式链接。涉及别名重叠时优先保留完整主题。个别常见词在原版也会成为链接，例如鱼类正文中的 `START`，本批保留原链接目标。

另有 28 个 `showtext` 标题、别名和摘要。摘要来自 `get_topics` 记录的首句，由 `GameInfo_Hotspot` 按布局限制为 53 或 92 字节再添加原生省略标记（`0x100048ea6–0x100048f4f`）。白鲑、木铲的原始标题与摘要由捕获日志确认。翻译与链接通过词表校验，游戏内显示与点击行为尚未验收。

后续通用摘要入口：运行时在 `GameInfo_Hotspot` / `toTex_GameInfo_Hotspot` 作用域记录主题，在原生 (15,552) 标题和 (15,563) 摘要位置查找 `encyclopedia-title` / `encyclopedia-summary`。软件 showtext 与纹理路径的 renshowtext 共用规则。非空自定义正文不套用主题摘要。`encyclopedia_summaries.json` 为30主题43别名提供完整短释义，不改百科完整正文。
