# 贤者、铁匠与技能自述

以下为 UrW 3.89.1 的静态虚拟地址。运行时处理入口为 `composeExtraDialogue(NSString*)`，接收标准化后的 `npc-talk` 单次发言，返回中文或 `nil`。规则在显示层使用，人物与地名通过原有解码后按捕获值显示。

| 生产点 | 句式和数据 |
| --- | --- |
| `PARSE_sage_around` (`0x1001877e0`) | 本地找到时在 `0x1001878aa` 显示 `Yes. We have our %s.`，然后进入人物位置问答。附近找不到时在 `0x10018795f` 给出完整否定答复。外村答复由 `0x100187972`、`0x1001879be`、`0x1001879ea` 三次显示组成。 |
| `PARSE_blacksmith_around` (`0x100187a20`) | 本地显示带姓名的回复，技艺值大于等于 85 时用 `Yes. We are proud to have %s %s as our blacksmith.`，然后进入人物位置问答。无结果在 `0x100187b75` 显示。外村在 `0x100187bd6` 显示含等级与路线的答复，在 `0x100187c02` 追加位置。 |
| `navitxt_Full` (`0x1000bae90`) | 两个外村问答都传入标志 `1`。方向用八方词表，允许直接方位 `directly in the`，接 `from here, ` 和距离。距离加 ` away`，按单位给整数或三个近程固定短语。步程用位 `2` 控制，这两条路径不会进入该分支。 |
| `navitxt_WorldLocation` (`0x1000bae30`) | 拼接 `terdesc(x,y,1)` 和 `HaetunAlueenKuvaus`。领地名来自 `_CULTURE_REGION` (`0x10023c930`)，内部方位来自 `cultgeodesc`，也可能给出无人区及与领地的相对位置。地区名由 `at the region called` 或 `here at` 引入，可含英文副名与引号。 |
| `CrTalk_skills` (`0x10017d4f0`) | 普通 NPC 在 `0x10017d7b0` 先显示 `I'm %s in hideworking `。在 `0x10017d9b3` 接续 `and %s with timbercraft.`，两项等级一致时省去第二个等级。贤者使用八条固定自述，铁匠在同一个末尾显示点使用技艺与成品等级自述。 |
| `taitoteksti_perus` (`0x1001b5fc0`) | 技艺值按四舍五入到十位后索引 `_SI_taitokuvaus` (`0x100247260`)，11 项，每项 100 字节。铁匠使用 `taitoteksti_seppa`，其可将大师等级改成 `skilled expert`。成品品质来自 `_laatuluokitus_ase` (`0x100246320`)。 |

武器技能自述走独立的 `CrTalk_weaponskills`。本地问答转入的通用人物位置对话也有独立的生产点。两者与此处的贤者、铁匠和生活技能规则分开。

可在 macOS 运行独立匹配测试。

```sh
clang++ -fobjc-arc -framework Foundation tests/dialogue_extra.mm -o /tmp/dialogue_extra_test
/tmp/dialogue_extra_test
```
