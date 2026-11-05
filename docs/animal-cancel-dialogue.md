# 同行反悔与购买动物

3.89.1 x86_64 对话显示链路依据 `build/disassembly.txt` 和现有捕获记录。词表在 `data/translations/animal_cancel.json`，动物动态句在 `src/animal_dialogue.inc`。

| 场景 | 显示入口与地址 |
| --- | --- |
| NPC 已答应同行，玩家在交付前反悔 | `CompanionRecruitChat` 在 `0x100186a43` 加入带引号的选项。列表由 `LIST_Draw` 调用 `showtext`（`0x1001503d0`），选中后 `Execute_Talk` 调用 `PlrTalk`（`0x100191ca2`）。`RunParser` 处理 `[RECRUIT CLEAR]` 后由 `CrTalk`（`0x10018d324`）显示答复。两处玩家文本及 NPC 答复均有捕获记录。 |
| 动物交易入口 | `0x100195160` 将 `B.Buy an animal` 加入列表。捕获确认快捷键 B 与正文分别绘制，词表使用 `Buy an animal`。 |
| 动物可售 | `Make_Animal_List` 在 `0x100189f42` 拼接尺寸和动物名。 `Execute_Talk` 把最多五项加入菜单，`0x1001913d8` 显示由 `andlist` 拼接的动物清单。 |
| 没有动物可买或找错人 | `0x1001915bd` 显示三种拒绝之一，`0x1001915ce` 加入不带引号的结束选项。 |
| 选择、报价与成交 | `RunParser` 读取原有 `#n` 参数，在 `0x10018c968` 显示报价邀请。`Show_Trade_Info` 绘制货物和报价栏。`Trade_Complete` 在 `0x10017fdbd` 显示交付动物及绳子的承诺，`0x10017fe65` 显示成交提示。 |
| 确认或取消报价 | 已有的 `generated_chat_options.json` 提供确认、重新考虑、重新出价和拒绝交易等选项。`generated_chat_resources.json` 提供资源型成交和接受出价答复。新增词表覆盖已确认的二进制内嵌交易答复。 |

共享的 `npc_trade_suggestion` 在 `0x1001818ef` 绘制报价引导，在 `0x100181966` 单独绘制任意物品拼成的报价清单。前一句使用固定译文。后一条只有从对应原生调用点进入显示时才按物品词表尝试整行翻译。动态动物句只匹配已知动物名与尺寸。无法识别的名字保留原文。

自动检查可运行 `python3 tools/validate.py` 和 `python3 -m unittest discover -s tests -p 'test_chat*.py'`。动态动物句可通过 `clang++ -fobjc-arc -framework Foundation tests/dialogue_extra.mm -o /tmp/urw-dialogue-extra-test && /tmp/urw-dialogue-extra-test` 检查。游戏内可在测试档先走“同行后反悔”，再找村民进入“购买动物”，分别核对无动物、动物清单、报价、重置报价、拒绝和成交。
