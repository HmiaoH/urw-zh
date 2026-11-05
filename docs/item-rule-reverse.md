# URW 3.89.1 背包名称生成：静态逆向

对象：macOS x86_64 `urw3-bin`，SHA-256 `124f89da263b7dabb323fd4f94718261abbe0ef76371a7e5ed5d6b50492ae112`。地址均为未加 ASLR 偏移的 Mach-O 虚拟地址。证据来自 `otool -tvV` 以及二进制的数据表和跳转表，未启动或修改游戏。下文的字段名是按用法命名的；裸偏移表示当前版本结构布局，不是存档格式。

可用 `python3 tools/analyze_item_rules.py /path/to/urw3-bin` 重新提取品质词、量词/植物词、跳转表以及截短调用点字节；脚本先核对二进制哈希，仅读文件和输出 JSON。

## 生成顺序

```text
showInvList
  ekuvaus(object_id, stack_count, 1)
    enimi(object_id, stack_count, 1)
      [品质／变质] + 基础名称（可能带材质／加工词）
      → 木种替换、winter 前缀、特例覆盖、绑定/配件后缀、植物分类
    → 容器 / 量词 / 长度 / 燃烧修饰；最后在 count >= 2 时添加数量
  → 交易附加状态
  → 选择键 / 部分选取数量
  → strmaxcut(row, 40)
  → LIST_ButtonSpotEntry
```

这里的品质放在 `enimi` 的最终拼接点（0x10004e61c–0x10004e63f），所以 `winter` 和木种处理发生在名称主体上，品质仍在它们之前。植物分支可覆盖此前生成的主体。“烤、烟熏、盐渍、风干”已存在于部分物品的基础字符串中；容器格式和量词可以把原本在行首的品质推到 `of` 后。

## `enimi(int object, int count, unsigned char flags)`（0x10004daf0）

- 从 `ObjToItem` 或（当 `object == -1`）`NimiTempItem` 复制 0xac 字节；`ItemStruct + 0x09` 是通常的基础名称。类别字节为 0x0c 时，直接使用 `NPC_ruhokuvaus` 的描述并提前返回（0x10004db89–0x10004dc22）；不要用常规基础名称语法猜尸体。其余类别中，`flags & 0x20` 且 `+0x78` 非零时改取所指内容对象（0x10004dc27–0x10004dc55）。
- `count >= 2` 调用 `mon`，但 `+0xa6 == 7` 或 ID `0x1cd` 跳过最初的复数转换（0x10004de31–0x10004de74）；带已知树种的木材分支稍后再按同一数量重算一次。这里没有添加数字。
- 木种只对类别 8、`+0xa6 != 7` 且 `ItemGet_puulaji`（读 `+0x6c`）非零生效；`flags & 0x40` 抑制该分支（0x10004de74–0x10004dea8）。默认格式 `%s %s`（树种、原名称）；ID `0xc9` 或匹配 `slender tree trunk` 改为 `slender %s trunk`。在原名称的小写副本中，先找 `wooden `，未找到再找 `wood `，用树种替换首次匹配的词；随后独立找 ` wood`，找到则保留之前的文字及空格、添加树种并丢弃匹配后的尾部。子类 `+0x08 == 0x16` 或 ID `0x191` 覆盖为 `block of %s wood`。最后若 `count >= 2` 再调用 `mon`（0x10004dec2–0x10004e0f1）。`TreeSpecies_txtdesc` 的跳转表（0x1001b5514）给出 1–6：`pine`、`birch`、`rowan`、`alder`、`spruce`、`aspen`。
- `+0x8d & 0x10` 加 `winter %s`；`+0x78` 非零时 ID `0x37` / `0x45` 把主体覆盖为 `water` / `milk`（0x10004e0f6–0x10004e15e）。
- 类别 6、子类 9 且 `+0x68` 的实体引用可解析时，`onko_NPC_lieassa` 产生 ` (%s leash)`；`is_tied` 产生 ` (tied to %s)` 并覆盖前一个后缀，调试开关还可附 ` (#%d)`（0x10004e162–0x10004e274）。
- `flags & 4` 未设时，ID `0xf9` 根据 `+0x88` 引用附 ` with no hook`，或按引用对象的材质掩码 `1`、`2`、`0x100` 依次附 ` with wooden hook`、` with iron hook`、` with bone hook`。这些检查不是互斥链。ID `0x78` 或子类 5 在 `+0x88 == 0` 时附 ` with no string`（0x10004e279–0x10004e376）。
- 类别 0x0b、ID `0x1ae..0x1b6`、`0x201` 或 `0x3d` 可进入植物名称处理。名字索引取 `+0x93`（`flags & 8` 则强制 1）；索引至少 2 时，以步长 30 的名称表覆盖主体并加类型名。`flags & 0x10` 对类别 0x0b 先选用 `+0x31`，并可使浆果分支加单数 `berry`。跳转表（0x10004e6a4）可见 `0x1ad` straw、`0x1ae` grass、`0x1af` berry shrub/berry（按类别）、`0x1b0` bean、`0x1b1` root、`0x1b2` seed、`0x1b3` grain、`0x1b4` leaf、`0x1b5` flower、`0x1b6` cereal、`0x201` mushroom；ID `0x3d` 走 flour，其余按类别选 plant/fruit。straw 目标在跳转表中存在，但当前入口条件对非 0x0b 的该 ID 不成立。bean、seed、grain、leaf、flower、flour 分支直接取表的复数；其他类别分支见 0x10004e445–0x10004e617。
- 最后用 `%s%s` 拼品质缓冲区及名称主体，返回小写临时字符串（0x10004e61c–0x10004e655）。

### 品质与状态

`on_laatutieto`（0x1000d1c40）读 `+0xa5` 最高位；`ItemGet_laatu`（0x1000d1c10）读其低三位，0 转为 3。显示分支把超过 5 的值按 5 查表；品质为 0/3 时不输出。类别 0x0b、ID `0x37/0x45` 或 `flags & 6` 强制为 0；类别 7 且 `+0x59 < 2` 先强制品质 2。根据 `onko_NUOLI`（0x10016c740，类别 1 且子类 6）和类别选择品质表（0x10004dc5a–0x10004dd68，分类指针表 0x1002381a8）：

| 条件 | 表地址 | 1 | 2 | 3（省略） | 4 | 5 |
| --- | --- | --- | --- | --- | --- | --- |
| 箭（优先） | 0x100246350 | curved | rough | decent | fine | superior |
| 1、4、6 | 0x100246320 | crude | rough | decent | fine | masterwork |
| 2 | 0x100246380 | crude | rough | decent | fine | masterwork |
| 3 | 0x1002463b0 | leaky | rough | decent | fine | beautiful |
| 5 | 0x100246440 | ragged | harsh | decent | fine | superior |
| 7 | 0x1002463e0 | awful | bland | decent | tasty | delicious |
| 其余 | 0x100246410 | poor | inferior | decent | fine | perfect |

类别 7、`+0x59 < 2` 的变质分支（0x10004dd6d–0x10004dddb）：若基础名已匹配 `*stale *`，清空前缀以免重复；否则写入 `stale`。非空前缀末尾加空格。随后 `+0x59 == 0xff` 无条件覆盖前缀（0x10004ddf1–0x10004de2a）：类别 5 为 `Rotten `，其他为 `Spoiled `，最终小写。因而 `curved`、`leaky`、`ragged` 在这些路径是品质等级；`stale` 和 `spoiled` 占用同一前缀位置。物品名中可另有加工词，例如 `roasted elk cut`；0x100077bec–0x100077c2f 在另一路分类逻辑中直接搜索物品名的 `SALTED `、`DRIED `、`ROASTED `、`SMOKED `，这些不是 `enimi` 的独立前缀生成分支。普通材质（如 fur、woollen、linen）也不能从 `enimi` 推导为任意组合；这里只有木种、配件掩码等特定分支。

### 复数

`mon(char*)`（0x1001b68e0）先复制成小写；如存在第一个 `/`，直接取其后的全部字符串（0x1001b695e–0x1001b6974）。否则依次按下表处理（空串直接返回）：

| 匹配 | 变化 | 证据 |
| --- | --- | --- |
| 尾部 `fe` | 替换为 `ves` | 0x1001b69bc / 0x1001b6b36 |
| 尾部 `f` 且前一字节在 `lr` 或 `aeiou` | 末尾 `f` 替换为 `ves` | 0x1001b69ea–0x1001b6a3a |
| `staff` 结尾 | 末尾 `ff` 替换为 `ves` | 0x1001b6a52–0x1001b6a75 / 0x1001b6b36 |
| 找到 `tooth` 且末尾是 `ooth` | 尾部 `ooth` 替换为 `eeth` | 0x1001b6a7b–0x1001b6aab / 0x1001b6b5d |
| 第一次出现 `lock of `（可位于 `block of ` 内） | `lock of ` → `locks of `，保留前后文字 | 0x1001b6ab1–0x1001b6b31 |
| 尾部 `x` 或 `ch` | 加 `es`（`ch` 需原长至少 3） | 0x1001b6b42 / 0x1001b6b78 / 0x1001b6bba |
| 尾部 `ry`（原长至少 3） | 尾部 `ry` 替换为 `ries` | 0x1001b6b8b / 0x1001b6bcb |
| 尾部 `s` / 其他 | 保留 / 加 `s` | 0x1001b6b9e–0x1001b6bb5 |

`yks(char*)`（0x1001b6c20）把第一个斜线截成 NUL，供明确调用单数的分支使用。普通 `enimi` 的单数分支直接复制基础名，并未在同一位置调用 `yks`。翻译器可用 `mon` **从已知基础名正向生成**候选，再检查碰撞；仅凭未知复数删尾或倒推会遇到多个候选。

## `ekuvaus(int object, int count, unsigned char flags)`（0x10004b610）

1. 读对象信息；和 `enimi` 一样检查 `flags & 0x20`。先复制 `enimi(object, count, flags)` 的结果（0x10004b733–0x10004b763）。
2. 若 ID `0xcd` 且 `ItemStruct + 0x68` 的 16 位值为 1，格式为 `burning %s`（0x10004b768–0x10004b7a3）。否则若 `+0x78` 指向内容，格式为 `%s of %s`：内容用 count、容器用 1，各自调用 `enimi`（0x10004b7a8–0x10004b806）。
3. 否则按 `+0xa6` 的跳转表（0x10004ba28）添加量词：0 无；1 `fistful`；2 `pinch`；3 `bunch`；4 `pile`；5 长度；6 `ball`；7 `sheet`；8 `bundle`；大于 8 回到 `fistful`。量词按 `count > 1` 用 `mon`，否则用 `yks`；原始单/复数字符串位于 0x100247180–0x100247240。数量词在 `%s of %s` 前半部。量词值 5 的分支虽构造 `%d ft of …`，但随后立即从原名复制回去，最终只附单位长度括号；量词值 6 先形成 `ball(s) of …` 再附同类长度括号（0x10004b88c–0x10004b9b0）。长度用 `+0x64` 调用 `UnitString_Length(float, 0)`，括号格式 ` (%s)`。
4. 最后 `flags & 1` 且 `count >= 2` 才生成 `%d %s`（0x10004b9c3–0x10004b9f2）；整个结果经 `StrLwr`（0x10004b9fa）。因此数字并非所有名称调用都带，选择了部分数量时出现的括号数字也不来自本函数。

## `Esineen_Raakanimi(unsigned char mode, ItemStruct)`（0x10007f500）

这是另一个用于取得物品名称片段/分类名的入口，背包行的上述调用链不经过它。它调用 `Luo_Esineen_Itempos`，再用 `enimi(pos, 1, 4)` 得到临时名；品质和配件后缀因此受前述 flag 限制，木种仍可保留。默认缓冲区由 `ItemMatSkill` 填充：后者初始取 `ItemStruct + 0x31`，植物有关分支可用 `KasvioPos` 后调用 `enimi(-1, 1, 0x12)` 换成草药表的名字，未找到写入 `unknown`（0x100066937–0x100066a14）。

0x10007f5e0–0x10007f6fa 另检查全局 `Item` 的 ID `0x1ea`、`tuntematon` 字面量、`SALTED ` 加鱼名判定及 ID `0x1fb`；在指定未知名称回退分支中，类别 7 的 ` cut` 可被用作截取点。不要把 `unknown` 和 `tuntematon` 当成同一个字节值。最后 mode `b` / `c` / `d` 分别覆盖为临时名的首词、末词、全名，其他值保留前面的分类名（0x10007f6ff–0x10007f745）。返回的是全局缓冲区 `_s_nimittaja`。此函数不能当成只读的背包名称恢复工具：`Luo_Esineen_Itempos` 会复用或建立对象位置，`ItemMatSkill` 还可能写 `_NimiTempItem`。

## 截短前的采集边界

`showInvList` 通过 0x100069271 的调用获取 `ekuvaus(object, stack_count, 1)`，复制到 `rbp-0x8e0`。当局部标记不含 0x10、交易上下文非零时，标记的 0x01、0x02 位按顺序加入 ` (unpaid)`、` (taken)`（0x100069285–0x100069301）。随后格式化 `%c.%s`；所选数量非零且小于堆叠数时改用 `%c.(%d) %s`（0x10006932d–0x100069375）。单独抓取 `ekuvaus` 返回值不能取得这三个列表字段。

可在 **0x100069389 调用前**只读复制 `%rdi` 的 NUL 终止行（当前栈槽容量 1024；`%esi == 0x28`），然后让原调用继续使用原指针和原长度。另一方案是带调用者过滤的 `strmaxcut` 入口，在返回地址为 0x10006938e 时复制后转发。原函数（0x1001b6bf0）以 `strlen >= 40` 为条件，在下标 38、39 写 `..`，并把下标 40 写 NUL，单位是字节；恰好 40 字节也会截短。

- 调用点的原 5 字节为 `e8 62 d8 14 00`。若采用调用点跳板，需要在 rel32 可达范围内并保留 ABI；若采用通用入口跳板，注意第 14 字节是相对 `call strlen` 的开头（0x1001b6bfd），当前通用的无重定位搬运方案不能直接覆盖它。
- 后续 0x1000693e2 的 `LIST_ButtonSpotEntry` 用同一栈行指针（`rbp-0x4e0`）。只在同线程、同作用域、同指针的下一条对应入口消费副本；列表重绘另需保存实际条目与译名的关联。不能把截短英文前缀作为唯一缓存键，因为不同名称可能截出同一行。
- 捕获副本应只交给显示层；原函数照常生成和截短，保留选择键、筛选、重量及原始列表数据。使用 `ekuvaus` 或 `enimi` 的临时 `sbuf` 结果时也必须立即复制，不能长期保存返回指针。

这里没有验证所有物品创建器的材质/加工命名来源、运行时植物名称表内容、长度单位切换或稀有分支的实际出现条件。分支存在与自然游戏中可生成是两回事；本文仅为静态规则和采集依据。
