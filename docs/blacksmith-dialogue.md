# 铁匠订购对话

`data/translations/blacksmith_dialogue.json` 保存固定对话，`src/blacksmith_dialogue.inc` 组合原生生成的选项和回复。显示层读取英文选项，原版仍用同一个订单索引选择商品和处理交易。

## 原版路径

| 场景 | 证据 |
| --- | --- |
| 打招呼、请求订购、被拒绝、已有订单 | `TryChatOption_Blacksmith` 与 `Blacksmith_Service_Query`。商品分类由 `0x100189c17–0x100189c3a` 组装，铁匠手艺由 `CrTalk_skills` 继续显示。 |
| 进入分类并挑选商品 | `Blacksmith_Tilausesine_Kategoria` 用 `an` 或 `mon` 生成单件或批量选项，`0x100189523` 加入列表，`0x100189606` 显示分类货品。玩家选项和选中后的发言都采用对应译文。 |
| 品质、工期、付款条件与取消 | `Blacksmith_Tilausesine_Valinta` 在 `0x100188e3a` 调用 `ekuvaus` 取得有品质及数量的物品描述，在 `0x100188efd` 调用 `TIMESPAN_days`。确认、询问付款或反悔是分开的选项。 |
| 询问付款、确认订购 | `BlacksmithTalk_Tilausesine_Hintakysely` 调用交易建议及报酬抵扣。`Blacksmith_Tilausesine_Hyvaksynta` 在 `0x100189315` 显示单件或一批货的订购确认和工期。 |
| 催单、完工、过期、制作失败 | `0x1001841bb–0x10018420b` 生成询问进度的选项。 `NPCpuhe_tilaus` 处理未完工、可交易、放在附近、长期未取或无法交货的分支。 |
| 取货议价、取消交易与成交 | 复用 `generated_chat_options.json` 和 `generated_chat_resources.json` 的交易确认、取消、成交及未取货回复，并复用已有议价提示。 |

## 商品表和时间格式

3.89.1 x86_64 的 `_BlacksmithDataList` 位于 `0x10023ee50`，记录大小 `0x8c`，商品名在记录起始处，分类在 `+0x60`，预计天数、技能门槛和件数分别在 `+0x80`、`+0x84`、`+0x88`。逐条读取后得到八类 31 项。可选产品由原版按村落文化和铁匠技能筛选。

- 刀具：刀、小刀、宽刃刀、猎刀、渔刀、考莫刀、北方刀、斯克拉马短刀。
- 工具：镰刀、锅、铲、铁鱼钩、铁缝衣针。
- 斧头：手斧、雕刻斧、劈柴斧、伐木斧、宽刃斧。
- 矛：矛、考莫矛、北方矛、安戈矛、三叉戟、宽头三叉戟。
- 其余：箭镞、宽头箭镞、短剑、阔剑、铁头盔、铁护目盔、圆盾。

铁鱼钩每批 6 个，箭镞及宽头箭镞每批 12 个。工期用本地 `messages/urw_defs.txt` 的 `.TIMESPAN_DAY.`，进度回复的补充时间语法来自 `DataReadyDesc`、`MintickDescInDays` 和 `AikaTeksti`。截图中的镰刀对话原文已对照现有捕获日志。共享议价函数在 `0x100181966` 单独显示付款物品清单。只有从该调用点进入 NPC 显示时才尝试组合译文，最多十项，保留数量、品质和穿戴状态。未知物品或格式会让整行使用原文。取货交易面板中其他共享报价或拒收分支沿用原有交易翻译。

固定词表、聊天生成器测试和 `tests/blacksmith_dialogue.mm` 的独立运行时断言已通过。其他品质、村落文化和交易分支尚未游戏内验收。
