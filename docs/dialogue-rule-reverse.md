# UrW 3.89.1 对话生成与翻译规则

以下地址来自本地 `build/disassembly.txt`，是 Mach-O 静态虚拟地址。证据来自反汇编、原始资源和草稿对照，覆盖范围以静态验证为准。运行时定位需按已校验的目标版本及 ASLR slide 解析。

## 三条文本路径

| 路径 | 证据 | 数据来源 |
| --- | --- | --- |
| 资源对话 | `CHATMSG(char*)` 入口 `0x1001b9190`，`0x1001b9229` 构造 `messages/%s_chat.txt` 并使用 `_language`，`0x1001b9649` 将已选正文复制至 1 KiB 的 `sbuf` 槽，`0x1001b9659` 调用变量解析器 | `messages/urw_chat.txt` |
| 一般消息表达式 | `MSG(char*)` 在 `0x1001b512c`、`0x1001b514b`、`0x1001b5160` 调用同一个角括号解析器，在 `0x1001b5134`、`0x1001b520a`、`0x1001b532a` 调用 `MSG_parse`。后者构造 `messages/%s_*.txt`（`0x1001b8bcb`），读取段名、条件分支和正文（`0x1001b8e15` 至 `0x1001b8f3c`），也有 `[HEAR:` 分支（`0x1001b8cd5`） | `urw_msg.txt`、`urw_combat.txt`、`urw_defs.txt` 等 |
| 原生对话 | 原生调用者组合字面量、`sprintf`、随机分支及格式生成器后调用 `CrTalk(char*)`（`0x10017a4b0`）或 `PlrTalk(char*)`（`0x10017b7e0`），由显示函数分行并绘制 | 可执行文件与游戏状态 |

`[IN_DIR:<npc_direction>]` 是一般消息表达式。内层变量给出罗盘缩写，外层按 `urw_defs.txt` 的 `.IN_DIR.` 分支选择方向文本。原生导航使用另一条链，读取 `_Ilmansuunta` 或调用 `navitxt_Dir`。两处的词形和标点应分别保留。

### 资源对话结构

`CHATMSG` 以 `.%s.` 查找主题（`0x1001b926d`、`0x1001b9336`）。请求形如 `TOPIC:many` 时，在第一个冒号处截断主题、存储后缀（`0x1001b929f` 至 `0x1001b92ce`），之后按后缀过滤候选行（`0x1001b9483`）。`(trading mood)`、`(stealing mood)`、`(mischief)`、`(overall rep)`、`(help rep)`、`(fam rep)` 等标题元数据由 `0x1001b934e` 至 `0x1001b9422` 的字面量探测处理。

正文从首个 ASCII `-` 后开始（`0x1001b9495` 至 `0x1001b94ba`）。之前的 `:(` 与 `:)` 分别进入数组低端与高端各三个槽，中性进入中间槽（`0x1001b94eb` 至 `0x1001b9561`）。选中的槽为空时回退至首个合格行（`0x1001b9566`、`0x1001b961e` 至 `0x1001b9631`）。`:|`、无前缀、`many: ` 在这一情绪分类中属于中间路径，`many` 同时受上面的请求过滤。编译器保留原行选择逻辑，显示匹配才去掉前缀。真实例子是 `chats_TimeBasedGreeting(int)` 在 `0x10018bb88`、`0x10018bbbd`、`0x10018bbe0` 分别请求 `GREET`、`GREET_MORNING`、`GREET_NIGHT`。

`Parseroi_vMSG_avaimet(char*)` 通过 `lue_tag(...,"<>")` 取变量名（`0x1001b905c` 至 `0x1001b9063`），调用 `Vaihtuva_MSG_Avain(char*)`（`0x1001b90ca`），拼接变量值与其余文本（`0x1001b90d9` 至 `0x1001b90fd`）。每次解析应立即复制变量值，解析器重用 `_vaihtuva_MSG_avain` 暂存区。

| 源占位符 | 已定位值 |
| --- | --- |
| `<plr_identity>` | `plraddress(_TARGET_NPC, 0)`（`0x1001b810a` 至 `0x1001b811e`），依赖说话者对玩家的称呼，可为名字或身份 |
| `<plr_bad_name>` | `plraddress(_TARGET_NPC, 1)`（`0x1001b8137` 至 `0x1001b8142`） |
| `<plr_name>` | `_Plr` 起始的角色名（`0x1001b814c` 至 `0x1001b816e`） |
| `<reptitle_trading>`、`<reptitle_stealing>`、`<reptitle_mischief_ind>`、`<reptitle_help_ind>` | `reptitle` 分支以 `tra`、`ste/the/thi`、`misch`、`hel` 选择已有声望称号（`0x1001b8173` 至 `0x1001b8265`）。`<reptitle_trading_ind>` 与 `<reptitle_tra_ind>` 共用 `tra` 路径，`ind` 调 `an()` 加英文不定冠词（`0x1001b829f`） |
| `<direction>`、`<npc_direction>` | 方向来源分支位于 `0x1001b7d7d` 和 `0x1001b7dbe`。`guide_values.txt` 说明分别为当前情境方向和 NPC 方向，值是 N、NE、E 等缩写 |
| `<var>`、`<status>`、`<weapon_slot>` | 分别读取 `_vMSG_var`（`0x1001b7e13`）、`_vMSG_status`（`0x1001b83bb`）、`_vMSG_weapon_slot`（`0x1001b7ff7`），整数走 `%d`。`vMSG_` 是内部变量来源之一，许多标记从游戏状态计算 |
| `%s` | 是另一阶段的 C 格式槽。消息传播分支先调用 `CHATMSG`（`0x10018f666`），用其返回值作格式字符串，将当事信息作为实参（`0x10018f681`），最后调用 `CrTalk`（`0x10018f689`） |

`urw_chat.txt` 在目录和三个草稿合计各有 79 个同 ID 条目、34 段，27 条静态文本、46 条带角括号占位符、6 条带 `%s`。所有草稿与目录的首个连字符之前的前缀和占位符多重集合一致。第一批可按三组编译。27 条静态行生成完整精确键。46 条身份、称呼及声望行生成命名槽模板。6 条 `WOM_BAD_INFO`、`WOM_BAD_NEWS`、`WOM_BAD_RUMORS` 行单独处理，区分默认和 `many`，并标注 `%s` 的二次格式化来源。草稿身份槽保留了数据流，声望称号及语序仍需语言审校。

### 硬编码导航与自报姓名

| 格式或分支 | 地址与实参来源 |
| --- | --- |
| `There is a %s in the %s %s.` | `PARSE_Etsimassah` 的 `0x100187d30`，实参顺序是调用者传入的目标种类、`_Ilmansuunta[_Suunta_Karttamerkki]`、`HaetunAlueenKuvaus(x,y)`，在 `0x100187d54` 显示 |
| `It is %s.` | `0x100187d67`，`EtaisyydenKuvaus(_Etaisyys_Karttamerkki)` 通过 `0x1001b630d` 调用 `navitxt_Dist(distance,0,0,0,9)`，在 `0x100187d7e` 显示 |
| `It is %s village.` | `0x100187dac`，标记类型等于字节 `0xef` 时，由 `get_kulttuuri(x,y)` 索引 `_CULTURE_ADJECTIVE`，在 `0x100187dc7` 显示。与宽泛的 `It is %s.` 存在匹配重叠 |
| `But %s there is a village with a sage.`、`Not here, but you can find a %s blacksmith in a village %s.` | `0x1001879a0`、`0x100187bb5`；共享 `navitxt_Full` 生成的导航短语，铁匠另有 `taitoteksti_seppa` 的技术等级 |
| `It's %s.` | `0x1001879d3`、`0x100187beb`，上一调用为 `navitxt_WorldLocation`。该函数在 `0x1000bae5f` 至 `0x1000bae76` 将区域描述与前一个位置片段按 `%s %s` 拼接 |
| NPC 自报姓名 | `KysyNimi` 在 `0x100183aec` 至 `0x100183b18` 从 `I'm`、`They call me`、`My name is`、`I am called`、`I'm known as` 中随机选引导语；在 `0x100183b39` 至 `0x100183b57` 用 `%s %s.` 拼接引导语和 NPC 名字并显示。相同组合在 `0x100183d42`、`0x100185c06`、`0x10018daa2` 重现。单独的 `p_mina_olen()` 在 `0x10017a741` 尾调用同样的随机池 |

`navitxt_Full` 在 `0x1000baec6` 调 `navitxt_Dir`，随后在 `0x1000baef9` 调 `navitxt_Dist` 拼接。距离存在数字单位和固定步程短语，例子有 `about %d kilometers`（`0x1000ba384`）、`about %d miles`（`0x1000ba3f7`）、`half a day's walk`（`0x1000ba5e8`）以及可追加的 ` or at least %d kilometers`、` or at least %d miles`（`0x1000ba669`、`0x1000ba697`）。`HaetunAlueenKuvaus` 可给出 `at the region called %s` 或 `here at %s`（`0x1001b624f`、`0x1001b625f`）。应把方向、距离、区域表达式和文化形容词分别作为有类型的子规则；动态地名和人名保留原值。每条规则记录生产点，因为不同分支共用通用英文句式。

### 选项和玩家回声

`AddChatOption(int,char*,char*)`（`0x10017b120`）第二实参为显示选项，第三实参是路由键。`0x10017b15f` 对路由键做比较，`0x10017b1a2` 使用显示文字参与重复判断。插入时将显示文字写入记录偏移 `+0x4`（`0x10017b1f8`）；自动编号分支使用 `%c.%s`（`0x10017b217`）；路由键写入偏移 `+0x68`（`0x10017b223`）。这给显示字串留下 100 字节的字段，且包括终止符和自动编号。示例 `"Yes, I know. How about more distant settlements?"` 与 `[LOOKING FOR DISTANT VILLAGE]` 是不同实参（`0x100187f1e`、`0x100187f25`）。保留游戏表和英文查重，翻译在菜单的绘制及玩家回声阶段分别执行。

## 编译策略

1. 按目录 ID 合并草稿，验证原文、段名、行号和文件内容一致。按来源解析三类语法，聊天资源保留情绪和选择器元数据，一般消息保留嵌套方括号和音效标记，原生格式以静态版本和已验证调用点登记。聊天翻译只提取首个连字符后的正文。读取资源时沿用目录声明的 CP437。
2. 编译源端为锚定的字面量与类型槽序列，目标端为字面量与槽引用序列。重复槽按原出现编号标识，目标允许重排。无来源记录的变量、占位符缺失、无法分隔的相邻自由槽、冲突的同输入异译都拒绝发布。保留原始格式中的空格，确需支持的尾部空白差异应按实际读取结果作为显式别名。
3. 首批可以在现有 `npc-talk`、`player-talk` 显示上下文中应用精确和唯一模板匹配。按首段字面量缩小候选，整行匹配并检验类型，检测多种切分和多个候选得到的不同译文，冲突时显示原文。优先为 `It is %s.` 一类通用格式加调用点约束，或限定槽须是可识别的距离短语。未知称号、姓名和地名按捕获的原编码值传递，不重新推导声望或随机结果。
4. 需要来源确定性时，在 `CHATMSG` 动态范围内识别 `0x1001b9659` 的变量解析调用，捕获已选的英文正文和该次解析返回的槽值；将这份元数据随当次显示关联。不要靠 `sbuf` 指针长期关联，调用者可 `strcpy` 到另一块缓冲区，例如问候的 `0x10018bb93`。对 `WOM_BAD_*` 需经过最终 `sprintf` 再关联，优先在显示处应用验证过的最终模板。保持原游戏字节串，避免未审查的翻译进入 `sprintf` 或持久存储。
5. 生成受限的显示缓冲，遵守各绘制和分行路径的实际字节边界。未验证的槽组合回退原文。测试至少覆盖 79 条静态展开样例、前缀分类、六个 `%s` 路径、含分隔符的人名和地区名、未知文化、空槽、不同度量单位、名称自报与普通 `I'm …` 的冲突、以及选项文本与路由键隔离。

## 可复现的导航候选清单

运行 `python3 tools/analyze_dialogue_rules.py`，从测试应用中的同版本 Mach-O 读取表项和原始字节，生成开发用 `build/dialogue-rule-candidates.json`。输出包含源可执行文件的 SHA-256、四条完整匹配模板、生成与显示指令地址，以及方向、地标类型、距离和文化的限定值。

- 方向表 `_Ilmansuunta`（`0x10023ed20`）的八个指针已按静态表顺序解码。地标分支从调用指令追溯到 `settlement`（`0x10018d7ea`、`0x10018d828`）、`lake`（`0x10018d869`）、`cave`（`0x10018d8d7`）。
- 地标距离专用调用的标志值是 `9`，在 `0x1000ba318` 走直接距离路径，在 `0x1000ba4b6` 跳过步程分支，最后在 `0x1000ba6c8` 加 ` away`。因此只给这条生产路径发布两种单位各四种短语候选，带数值的短语保留原数字。
- `_CULTURE_ADJECTIVE`（`0x10023c850`）的十四项均记录原始字节。有三个词含字节 `e4`，候选文件以十六进制精确保存，避免从资源文件的 CP437 声明推断二进制字符串编码。仅 `kuikka-tribe` 带已有审校译名，其余文化值等待审校。
- 已在游戏显示调用观察到的英语例子是 `There is a settlement in the south-west at the region called Nuokkukallio "Nodcliff".`、`It is just a couple of miles away.` 和 `It is kuikka-tribe village.`。其它组合来自静态反汇编与表项，JSON 中的目标文字是开发候选。
