# 物品名的展示入口

静态分析对象为 macOS x86_64 UrW 3.89.1，SHA-256 为 `124f89da263b7dabb323fd4f94718261abbe0ef76371a7e5ed5d6b50492ae112`。地址均为未加 ASLR slide 的 Mach-O 虚拟地址。依据为 `otool -tvV` 反汇编、对应可执行文件字节及游戏消息资源。

## 背包和手持栏

| 界面 | 名称生成 | 展示边界 |
| --- | --- | --- |
| 背包及经过同一入口的物品选择列表 | `showInvList` 的 `ekuvaus(object, count, 1)` 调用位于 `0x100069271`，随后组合列表字段并截短至 40 字节。 | `LIST_ButtonSpotEntry` 调用于 `0x1000693e2`，返回 `0x1000693e7`。详见[截短前的采集边界](item-rule-reverse.md#截短前的采集边界)。 |
| 手持武器及工具 | `Nayta_Wieldatut(int)` 从 `0x100130690` 开始，以 `getwieldedItempos(-1, slot)` 取两个槽位，在 `0x10013086f` 调用 `ekuvaus(object, 1, 0)`，复制后在 `0x100130887` 截短至 30 字节。 | 非空槽专用 `TekstiPalkki(x,y,width,text,4)` 调用于 `0x100130829`，返回 `0x10013082e`。`TekstiPalkki` 入口为 `0x100158030`，其中唯一的 `showtext` 调用位于 `0x100158601`，返回 `0x100158606`。 |

手持栏的标题和空槽各自调用同一个 `TekstiPalkki`，调用点分别为 `0x100130774` 和 `0x1001309d2`。绑定以已核对的函数入口及调用者为边界。非空槽内，游戏先绘制独立键帽，再用原文绘制条框并计算文本位置。组合器仅处理该次字形绘制中的完整物品名。对于 `rough woodsman's axe`，现有词表中已有 `rough` 与 `woodsman's axe`。

盾牌可能在第二次截短（`0x1001308d8`，25 字节）后附带 ` -- CENTER`、` -- HIGH`、` -- RIGHT` 或 ` -- LEFT`（`0x1001308e4–0x10013098f`）。这些附注和含 `..` 的截短行继续由原游戏显示，因当前完整物品名语法没有盾姿和截短恢复规则。若将来恢复长名，第一处截短调用前的栈副本可提供完整英文，调用后的字符串仍需保留以便原生布局。

## 通知面板

- **装备武器。** `Wield(int,int,unsigned char)` 将武器槽写入 `_vMSG_weapon_slot`、物品对象写入 `_TARGET_ITEM`。随后分别在 `0x100062c56` 和 `0x100062cea` 调用 `MSG("WIELD_WEAPON")`，再调用 `Note`（返回地址 `0x100062c63` 和 `0x100062cf7`）。`messages/urw_combat.txt:24–32` 定义 `HANDMODE` 的 `primary` / `secondary` 值，以及玩家句型 `[PC:+<the_fullitem> wielded as a [HANDMODE:<weapon_slot>] weapon.]`。原生通知输入带棕色控制前缀 `+`。两种展开句型的物品槽可以独立交给组合器，保留原文用于游戏状态和日志。NPC 的另一个分支有不同的外层句型。
- **看见地面物品。** `Display_Items(int,int,unsigned char)` 入口位于 `0x10013d4d0`。与玩家同坐标时写入 `here`，否则写入 `there`（`0x10013d503–0x10013d546`）。普通物品在 `0x10013d909` 调用 `ekuvaus(object,count,1)`。单一地面条目使用 `#You see %s %s.`（`0x10013df94` 或 `0x10013dfff`），后一分支先在 `0x10013dff0` 调用 `an(char*)`。两支都在 `0x10013e021` 调用 `Note`，返回 `0x10013e026`。数量为 7 的单组木桩对应 `#You see 7 wooden stakes here.`。词表已有 `wooden stakes` → `wooden stake`，并可用 `wooden` 和 `stake` 合成。该调用也可接收非物品描述，因此仍须验证完整句型和物品槽，未知描述整条回退。
- **多个地面条目。** 标题通知在 `0x10013d7fe` 提交，格式可为 `#Things that are %s:` 或 `#There are several objects %s:`。逐条描述在 `0x10013dfd8` 提交（返回 `0x10013dfdd`）。这一出口还可收到其他地图对象或加工状态描述，只有完整名称成功匹配时才适合直接复用组合器。进入格子的移动路径在 `0x1000c1b8c` 调用 `Display_Items`，查看位置的路径在 `0x10013eb13` 调用它。

## 其他已确认的展示路径

- **议价面板。** `Show_Trade_Info` 用 `ekuvaus(object,count,1)`（`0x10017c162`）生成玩家出价行，在 `0x10017c17a` 截短至 28 字节，由 `0x10017c197` 调用 `showtext`（返回 `0x10017c19c`）。议价目标的 `showtext` 返回点是 `0x10017c0ce`，输入为全局 `_Trade_Item`，这一缓冲区的所有写入分支尚未核对。
- **背包内的物品部件菜单。** `InvSel` 在 `0x10005fcf0` 调用 `enimi`，随后用 `Remove the %s` 构造选项（`0x10005fd1c`），交给 `Valinta_Lisaa`（`0x10005fd39`）及 `TeeRMValinta`（`0x10005fd52`）。选项需要按专用句型处理。该函数中的另一处 `enimi` 调用（`0x10005e8c9`）会将名称交给百科索引 `istopic`，同一个名称生成函数因此也服务于英文内部查找。

这些地址用于定位展示路径。交易和物品部件菜单只完成静态定位。通知的像素历史和原生行边界见[通知规则逆向](notification-rule-reverse.md)。

## 选择窗口提示与筛选标签

`InvSel` 把选择提示分成三次软件绘制。首次绘制固定的单选或多选提示，`0x10005de47` 单独绘制动作词，`0x10005de76` 绘制句点。动作词从已确认的选择窗口绘制点进入 `inventory-action` 词表。窗口标题、分类标题和“没有可用物品”的提示按完整字符串查找。

`InvSel` 在 `0x10005e6fb` 将固定分类填入 `Viewing: %s`，随后在同一位置覆盖一次前缀并换色。所有筛选标签使用同一中文前缀，保留原生颜色分界。

## 制作用料与暂停操作

手工制作主菜单在 `0x100056cc2–0x100056d8e` 构造十三个内置分类。制作前用料说明走段落绘制（`0x10007e054`），工具条目由普通软件文字绘制。制作要求通知保留 `0x10007e978` 格式化的条目编号，必需与可选工具有不同句式。优先工具、已选工具和工具品质都查询现有物品规则，缺少词条时原生消息仍可显示。

`ProceedPause` 在 `0x10012c5dc` 调用按键板绘制。该按键板逐字绘制 `[SPACE] to continue -- [ESC] cancel`。本地化只在这个调用点替换两段文字，原生按键字样、背景、位置和输入处理保持一致。

## 原生制作子菜单与材料数量

建造和手工子菜单分别从 `biy_glossary.txt` 与 `diy_glossary.txt` 提取了建筑与配方名。烹饪配方来自 `cookery_glossary.txt`。子菜单条目与制作窗口大写标题分别使用完整字符串。原生菜单的 `#标题: 选项` 通知要求标题和选项均命中制作专用词表。

`Esita_Tarvikelista` 在 `0x10007e0f7` 绘制完整材料行。材料行可能包括计量、单项数量和总量，例如 `4 ft tying equipment * 4` 和 `Wooden stake * 8`。同样的材料表达式也可出现在编号通知中。运行库先验证整行语法，再匹配已知材料名称，原样保留数值并翻译计量单位。未知名称或表达式沿用原文。

## 原生技能与制作操作

配方资源只列出材料与配方，原生技能操作还来自 `Toiminta(int)` 的 90 个命名分支（`0x1001ba870` 附近）。运行词表逐条核对该函数的非空字面量，并对照以下菜单构造入口补充直接标题和操作项。

| 菜单 | 直接字面量或入口 |
| --- | --- |
| 烹饪与五类配方 | `Cook`，`0x100044877–0x100044ab7` |
| 衣物四类与修补 | `Clothes_MainMenu`，`0x100054ad1–0x100054beb` |
| 陷阱建造、布设和维护 | `0x10000ab1f–0x10000ac20` 及 `Toiminta` |
| 纺织、枝条与肌腱加工 | `0x10005522f–0x1000552fd` 及 `Toiminta` |
| 农耕与皮革加工 | `agriculture`、`HIDEWORK` |
| 捕鱼、制弓、木工与草药学 | `Fishing`、`bowyer_items`、`wooden_items`、`Herblore` |
| 装柄、捆扎用具与网具 | 手工菜单的分类分支及 `Toiminta` |

配方数量由 `Lisaa_esine_menuvalinnat` 在 `0x1000510f2` 或 `0x10005116d` 另行格式化，例如 `Wood slat (20 pieces)`。整行到达 `showtext` 后再匹配已审校的配方名及正整数，保留数字。选中这类配方时，确认通知复用同一规则。
