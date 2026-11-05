# 百科材料与工具条目

`data/translations/encyclopedia_materials.json` 收录了本地 3.89.1 游戏资源 `build/test-home/GAME.NFO` 中 22 页的 103 个正文显示片段，共 168 个可点击链接。词表记录每个片段的原始页头、资源行号和读取分片。百科页的标题与空行继续由原生程序处理。

| 类别 | 已翻译的页 |
| --- | --- |
| 护甲与衣物 | `ARMOUR MATERIALS`、`LAMELLAR`、`MAIL`、`IRON`、`FUR`、`LEATHER`、`WOOLLEN.WOOL`、`BIRCH-BARK` |
| 纺织材料与工艺 | `CLOTH`、`NETTLE`、`FLAX`、`HEMP`、`LINEN`、`YARN`、`NALBINDING.NALBOUND`、`TENDON`、`SINEW FIBRE` |
| 工具与捆扎用品 | `SPINDLE`、`NETTING NEEDLE`、`CLOTH CORD`、`CORD`、`LEATHER ROPE.ROPE.ROPES` |

`show_topic` 以 150 字节缓冲区读取正文，然后调用 `link_show`（`0x10004a264–0x10004a30b`）。`fgetstr`（`0x100100fc0`）调用 `fgets`，去掉 CR、LF，单次最多读 149 字节。因此 `GAME.NFO` 第 3497、3504 行各匹配两个片段。词表原文按运行时 Latin-1 回退保留原始高位字节，译文中的 `<br>` 与原文对应。检查了原文标准化后的全资源重复项，本批片段均唯一。

`get_topics`（`0x100049499–0x10004951a`）按句点拆出页头别名，`Lisaa_Linkit`（`0x100049689–0x1000497fe`）按主题表逐个查找首次出现的位置、检查相邻字符，并排除当前页别名。链接审校使用本地 `debug_topics.txt` 中的主题表和上述边界条件。词表的 `evidence.source_link_candidates` 记录保留的源词。重叠匹配优先采用较完整的主题，例如 `SINEW YARN` 优先于其中的 `YARN`。包含重音字符的三个族名链接采用同一页头的 ASCII 别名 `DRIIK`、`REEMI` 和 `KIESSE`。

已通过词表、目标别名校验和百科链接单元测试。原生链接是否因屏幕折行而改变优先级，以及实际点击行为，尚未在游戏界面验证。
