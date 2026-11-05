# URW 简体中文显示适配

当前是 **macOS 3.89.1 渲染原型**，不是完整汉化发行版。只适配项目绑定文件中的 x86_64 游戏二进制。使用 C++/Objective-C++、CoreText 和游戏现有的 SDL2；不改写物品标识、配方或存档文本。

已实机看到中文主菜单、两段键盘帮助、带数字的日期，以及保留红色的完整消息“这里没有可以拾取的物品。”。新增的创建角色选项、性别、状态标签、百科操作说明及“村庄”开局正文也已实机显示中文。运行词表现有 394 条记录，其中 64 条按键或符号原样保留；这不是整游汉化率。全量初译和分类进度见 [覆盖报告](docs/coverage.md)、 `python3 tools/coverage.py` 与 [文本工作流程](docs/text-workflow.md)。大量译稿尚待语义审校与显示入口接入。

## 构建与隔离测试

需要 macOS Command Line Tools、Python 3，以及已安装的 URW 3.89.1。游戏路径在 `tools/bind.py` 中配置。

```sh
python3 tools/bind.py
python3 tools/validate.py
python3 tools/build.py
python3 tools/test.py
python3 tools/run_test.py
```

`build/urw-zh/liburw_zh.dylib` 是构建产物。测试启动器把游戏数据复制到 `build/test-home`，创建 `build/UrW-ZH-Test.app`，只使用该目录中的测试角色，不导入你的现有角色。`build` 包含本机游戏副本和测试存档，**不能作为发布包分发**。

```sh
python3 tools/run_test.py --prepare-only
python3 tools/run_test.py --english
python3 tools/configure.py en
python3 tools/configure.py zh
```

`configure.py` 更改构建产物的配置；运行时每秒检查一次。重新打开菜单后可以对照原文，游戏已缓存的面板和消息历史不会立即重绘。完整切换应退出后重新启动。`--english` 完全不加载汉化库，用于原版回读测试。

## Steam 启动脚本管理

当前仅做过真实目录的预检查，**尚未安装到 Steam 游戏目录**。原型仍有下述限制，建议先用隔离测试入口。

```sh
python3 tools/install.py install --dry-run
python3 tools/install.py install
python3 tools/install.py status
python3 tools/install.py uninstall --dry-run
python3 tools/install.py uninstall
```

安装器只替换启动脚本中的游戏执行语句。启动时核对二进制 SHA-256；不匹配或模块缺失时走原始英文启动路径。动态库再次核对 SHA、符号和钩子指令。

原始启动脚本和哈希保存在应用的 `Contents/urw-zh-backup`。卸载前核对当前脚本与备份；遇到 Steam 更新或用户修改时拒绝覆盖。卸载后的模块、配置和日志移入备份目录保留。重复安装不会覆盖已有配置。真实 Steam 启动、更新后回退和卸载仍需实机验收。

## 翻译格式

`data/translations/*.json` 使用稳定 ID、来源、上下文、原文、译文、审校状态。运行时只加载 `reviewed` 项，原译文相同的按键记录直接使用原版字形。匹配顺序是上下文精确、全局完整句、指定上下文动态模板。

```json
{
  "id": "example",
  "source": "runtime-capture",
  "context": "showtext",
  "kind": "template",
  "original": "Day {day:int} of {week:int}th week before midsummer point",
  "translation": "距仲夏 {week} 周，第 {day} 天",
  "status": "reviewed"
}
```

参数类型为 `int`、`number`、`text`，模板锚定完整句子，不支持任意正则表达式。多个模板同时匹配时保留英文。参数只从原文复制到独立译文缓冲区，不做全局词语替换。校验器检查重复项、模板参数、printf 占位符、控制标签和显式 `preserve` 字段；语义与上下文仍需人工审校。

`python3 tools/extract.py` 提取原文候选到 `research/catalog.json`。候选包含尚未分类的二进制内部字符串和资源语法，不能作为汉化覆盖率分母。运行时记录在模块目录的 `logs/captured.jsonl`；记录中的匹配标记也不能等同于实际绘制成功率。

## 当前限制

- 消息框支持短句的独立换行；超出消息框的译文完整回退英文。超长消息分页尚未实现，消息内多色控制也未完成验证。
- 百科的超链接位置、图文混排、全部长文滚动尚未适配验收。
- 短标签目前按原控件宽度缩放，窄控件可能影响可读性；部分软件绘制路径受游戏原生低分辨率限制。
- 使用系统苹方字体；不复制或分发 Apple 字体。尚未加入可再分发字体及其许可，发布打包入口未完成。
- 保存/读取的初步操作使用独立角色；原版回读、角色状态逐项一致性尚未完成验收。
- 创建角色和开局已接入部分译文；物品、制作、战斗、交易、任务、对话与百科的大批译稿仍在草稿目录，尚未完成运行时覆盖。

具体进度见 [实机验收记录](docs/verification.md)。

背包已接入限定在物品列表绘制中的组合规则，规则、实机样本和未覆盖形式见 [背包组合汉化](docs/inventory-composition.md)。
