# 足迹与追踪补充

## 原文和生成规则证据

- `data/catalog/binary.json`，`0x100232a3e`–`0x100232b10`：足迹年龄、`running `、`limping `、`Here you notice %s %s %s`、三种路径结尾。
- `build/disassembly.txt` 中 `Tutki_Datajaljet(int, int, DataStruct)` (`0x1001c0c80`)：
  - `0x1001c0cb7`–`0x1001c0d12`：先写入 `running `，跛行标志随后以 `limping ` 覆盖；最后附加 `tracks`。不存在同时出现两种步态的原生输出。
  - `0x1001c0dc9`–`0x1001c0e4d`：物种前可有 `_defs_ADJ_PIENI` / `_defs_ADJ_ISO`，即 `small ` / `big `；人类使用 `human`，其他生物用小写原生名称。未知生物为 `unknown`。
  - `0x1001c0e7d`–`0x1001c0f06`：九种年龄为 `very fresh` / `fresh` / `quite fresh` / `an hour old` / `some hours old` / `half a day old` / `day old` / `few days old` / `old`。
  - `0x1001c0f06`–`0x1001c0fa2`：年龄、带大小的生物、带步态的 tracks 依次拼接，再加 ` leading %s`、` which are numerous and mixed` 或 ` mixed with some other unclear tracks`，加句号后调用 Note。
- 野生生物名称来自原生二进制的 creature 定义字符串（catalog 中 `Hare`、`Arctic fox`、`Wild boar`、`Forest reindeer`、`Black grouse` 等附近）；家畜继续复用 `animalDescription` 的有限词表。
- 追踪消息资源：游戏 `Contents/Resources/messages/urw_msg.txt` 的 665、668、671、674、677 行分别是无足迹、发现足迹、附近足迹和两种水域提示，现有 `generated_notifications.json` 已收录。
- 搜索提示 `You walk around a little looking for tracks...`、远处足迹提示现有 `notifications_followup.json` 已收录。
- 此次 `tracking.json` 只新增 catalog 已证实而现有翻译未收录的两句：`:As roaming ahead something suddenly captures your attention.` 和 `+You have improved in tracking!`。不翻译内部 `TRACKS_FOUND` 等消息键。

## 行为与验证

`notificationTracks` 扩展有限生物名称和 `small` / `big` 修饰，继续要求完整原生句型。未知年龄、大小、物种、步态、方向和尾部附加文本全部返回 nil，由游戏保留英文。

`tests/tracking_assertions.inc` 应放在 runtime_test.mm 的 `zh::loadCatalog();` 之后。断言覆盖 9 年龄 × 8 方向、大小/步态/混杂足迹、有界生物词、全部追踪提示与未知输入回退。

本次使用临时 runtime_test 副本包含该断言编译，运行成功（完整现有 runtime 断言亦通过）；`python3 tools/validate.py` 为 6687 entries, 0 errors。未做真实游戏截图验证，所有新增资源保留 `runtime_verified: false`。
