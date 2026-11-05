# 原文目录与翻译覆盖

本项目区分三个指标：原文是否已有完整译稿、译稿是否经过审校、译文是否已在游戏中正确显示。提取成功、词表匹配成功均不等同于汉化成功。

## 目录

- `data/catalog/sections.json`：313 个 GAME.NFO 主题和 9 个 gameinfo 界面说明。按 `***` 分段，保留主题别名与图片元数据，正文不含开发注释与图片指令。目录页的链接文字保留在正文中。
- `data/catalog/scenarios.json`：13 个开局，每个包含标题、摘要、正文，共 39 条。
- `data/catalog/messages.json`：984 条消息源表达式。条件选择器、代词函数、控制标记和参数仍保留；这些不是展开后的可直接匹配句子。
- `data/catalog/labels.json`：323 条技能、建筑、配方、原料、用途说明及植物显示名称。只用于显示翻译；不会覆盖游戏中的配方引用。
- `data/catalog/binary.json`：10,026 条二进制字符串候选。包含内部标识、日志、资源路径和玩家可见文字，必须分类；不直接作为汉化率分母。

这些已知资源目录合计 1,668 条，不代表游戏全部玩家可见文字。标题别名的显示、动态组合后的物品名、任务分支、剧情对话及运行时新出现的文本仍需结合二进制与游玩捕获检查。历史更新日志、模组语法教程、随机姓名数据不作为翻译覆盖分母。

## 可复现操作

```sh
python3 tools/extract_sections.py
python3 tools/extract_resources.py
python3 tools/extract_labels.py
python3 tools/extract_binary.py
python3 tools/check_drafts.py --require-complete
python3 tools/audit_capture.py
python3 tools/coverage.py
python3 tools/report.py
python3 tools/compile_reviewed.py
python3 tools/build.py
python3 tools/test.py
```

提取器基于本机已安装的游戏生成原文；不修改游戏资源。`research/batches` 是可再生的分工文件。译稿保存在 `data/drafts`，只有经过审校且适配了显示入口的条目才进入 `data/translations`。二进制候选中的 `exclusion_reason` 只是分类建议，仍需核对来源，不能自动算作已覆盖。

`check_drafts.py` 比对源字段、标签、数值、URL、消息括号和行首控制标记，并调用词表校验器检查 printf 参数。源文中的数字字面值保持阿拉伯数字，英文拼写数词译为中文数词。纯百科、剧本和界面说明中的百分号不是 printf 参数。

`compile_reviewed.py` 目前只编译已审校的 gameinfo 段落和开局文本，不发布百科或消息表达式草稿。开局正文仅在完整原文一致时容许游戏额外插入的 `<br>`；外围空行仍保留，用于避让图片。其他段落保留严格标签匹配。

## 编码

资源目录采用 CP437 解码，保留可读的芬兰语字母。游戏运行时同时存在 Latin-1 姓名等字节串；通用捕获继续用 UTF-8 优先、Latin-1 回退，避免把人物姓名误解码。编译器将已知 CP437 资源的匹配键转成同一字节表示，译文保持 UTF-8。旧帮助记录中的 `ø` 是捕获的原始字节键，显示译文使用正确的 `°`。

## 打包边界

构建产物只复制配置、绑定和已接入词表，不复制完整原文目录或草稿。`build/test-home` 含游戏副本与独立测试存档，不得加入发布包。当前还没有可发行的完整汉化包。

本轮补提了旧规则漏掉的133条短字符串（含两字母词、方位、单位和简短对话片段）。全量目录首轮处理完成仍不代表所有排除理由或译文语义已审校。

## 经逆向确认的规则编译

`build.py` 自动运行 `compile_dialogue_rules.py`、`compile_chat_options.py`、`compile_chat_resources.py` 和 `compile_notification_resources.py`，再执行校验与构建。规则输入位于 `data/rules`，产物位于 `data/translations/generated_*.json`，不应手改产物。

交谈选项只处理 AddChatOption 的显示参数，NPC 回复按已确认的情绪/选择前缀解析，通知仅编译经过审校且槽边界可判定的表达式。不自动展开任意嵌套条件、代词或多自由文本槽。来源证据保留在生成记录，覆盖报告同时识别顶层 source_id 和 evidence.source_id。
