# 方向选择与地图地名

基于 3.89.1 的 `build/disassembly.txt` 和 `data/catalog/binary.json`。

- `ValitseLokaatio`（`0x10012e1d0`）在方向选择模式下先用 `StrUpr` 生成大写标题，再把 `Select %s` 和方向键及鼠标说明送入同一段落。原始参数在 `StrUpr` 后保持原样，所以段落目标仍为小写。方向标题和段落各按完整原文匹配。
- 方向参数来自 `OtaKohta_Suunta`、`OtaTyhja_Suunta`、`DirSel_ch` 和直接调用。固定参数覆盖门、陷阱、捕鱼、采收、木工、施工、捡拾、攀爬、踢击、战斗、观察和生火。关门和通用的目标选择已在 `screen_followup.json` 收录。宠物目标选择走 `CHOOSE TARGET` 分支。
- `CurrentMapName`（`0x1000a8b20`）根据地图位置组合可选地形、芬兰语地名和引号中的英文释义。地图底栏在 `0x1000ab3d4` 进入 `centext`，此时仍有未折行的完整文本。只在这个调用点拆出地形，地名与英文释义整段保留。文化村落的类型由 `_terrain[0xef]` 提供，前缀来自 `_CULTURE_ADJECTIVE`。
- 地图区域图上的独立地形名经 `karttapaikka_teksti` 写入 `regstat_terrain` 槽，随后由 `SlaveRender` 传给 `NewShowtext`。槽名和字段位置用于确认文本来源。同样的单词出现在别的界面时，仍由该界面自己的规则处理。

原生函数继续读取原始英文。地图绘制层从 `terrain-name` 字典按完整名称取译文，图块名、存档、玩家自定义地名和查找键保持原样。
