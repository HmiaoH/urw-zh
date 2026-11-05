#!/usr/bin/env python3
"""Write a reviewable progress snapshot, explicitly avoiding a whole-game percentage."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from bind import ROOT
from coverage import report
if __name__=='__main__':
    r=report();groups=r['resources'];families={}
    for source,g in groups.items():
        family=('开局剧本' if source.startswith('RNDCAMP.') else '消息源表达式' if source.startswith('messages/') else '百科主题' if source=='GAME.NFO' else '界面说明' if source.startswith('gameinfo/') else '名称与用途说明')
        totals=families.setdefault(family,dict(total=0,translated=0,reviewed=0,runtime_verified=0))
        for k in totals:totals[k]+=g[k]
    lines=['# 汉化覆盖进度', '', '更新时间：'+datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='minutes'), '', '**这不是整游汉化率。** 下表只统计已建立来源目录的资源文本；译稿存在、审校通过和游戏内验证分别统计。', '', '| 资源类别 | 条目 | 有译稿 | 已审校 | 实机验证 |','| --- | ---: | ---: | ---: | ---: |']
    for name,g in families.items():lines.append(f'| {name} | {g["total"]} | {g["translated"]} | {g["reviewed"]} | {g["runtime_verified"]} |')
    b=r['binary_translation_queue'];d=r['runtime_dictionary']
    lines+=['', f'二进制另有 {r["unclassified_binary_candidates"]:,} 条候选：{b["translated"]:,} 条有译稿（含 {b["passthrough"]} 条专名、符号等原样保留），{b["proposed_exclusions"]:,} 条标注了内部文本等排除建议，{b["untouched_candidates"]:,} 条尚未处理。排除建议仍需审校；重复用途、词语拼接和动态展开必须结合调用链核对。', '',f'运行词表共 {d["records"]} 条：{d["exact_records"]} 条精确匹配记录、{d["dynamic_template_records"]} 条动态模板。其中 {d["passthrough"]} 条按键/符号原样保留。词表规模不是实际显示覆盖率。', '', '动态消息源表达式已有译稿，但尚未全部编译为可验证的运行时模板。百科的链接布局、复杂物品名、对话和任务分支也未完成全面接入。尚无完整、固定游玩路径的漏译率，因此不报告整游百分比。', '', '完整性校验：`python3 tools/check_drafts.py --require-complete`。该检查只证明每条候选有译稿或分类理由，并检查参数/标签/源字段；不证明翻译准确或实际显示成功。', '', '捕获审计：`python3 tools/audit_capture.py`，检查被建议排除的原文是否曾进入绘制函数。零冲突仅覆盖已有捕获，不能证明全部排除正确。', '', '实机范围与限制见 [验收记录](verification.md)，来源与操作见 [文本工作流程](text-workflow.md)。','']
    (ROOT/'docs/coverage.md').write_text('\n'.join(lines))
    (ROOT/'docs/coverage.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(ROOT/'docs/coverage.md')
