# 仅修代表子集目录闭合；保留已接通统一入口

task_id: R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014_1616
execution_host: ZHANGWEI
SAM: HOLD
status: READY
phase: BENCH_CLOSURE_FIX_NO_TARGET_WRITE

## 审核结果
1518报告/合同/子集manifest/统一入口/reader/runner/winio/state/验收/3项test_formal_chain已读。
8个改动运行模块及入口测试SHA独立核对一致，连同已固定旧依赖重算code_digest=9b5ae88dd66b550d3e73eaabb2366c8682a2ffadd33e6b207e974d03fc950a22一致。
3项统一入口测试在Linux禁止真API环境独立通过（仅Windows C状态路径条件作隔离便携适配）：完整copy->accept/rerun、未授权/错盘/坏digest/超预算/越界拒绝、空/部分accept失败均成立。新元数据observe/显式唯一hash路径有效，可保留。
BENCH_SUBSET.sqlite约8MiB二进制未能经连接器读取内容，实际5032实体/5039文件/1023目录/3715链接与SHA为本机回报与manifest，不冒称ChatGPT已直接扫描实际库。

## 唯一阻塞：真实子集生成器目录闭合缺陷
用原build_subset在小SQLite fixture独立复现：
- 源有 E:\BLACKBOX\empty_target 普通空目录；
- junction指该目录，content_files=0；
- 生成器纳入该junction并标闭合；
- BENCH_SUBSET.links有映射target，但paths中没有target普通目录。
代码只 dirs.add(parent(link_target))，不加link_target自身；link path/target的全部父也没有统一补入。
Windows可以创建指向不存在目录的junction，现有full_acceptance比较target文字不等于证明target存在。不能在这种子集上把“链接闭合”或测速作为有效结果。

本轮只修这一组问题，不新建入口/框架/故障场景。

## 完成要求
1. 本机现有BENCH_SUBSET先mode=ro统计：
   每个link映射target是否对应明确普通目录、link父/target父各祖先是否有目录行，源正式计划target本身的实际类型（普通目录、另一个链接、未知）。
   给缺target/缺祖先的精确计数及少量例子。不假定真实3715全坏，也不拿小fixture代替实际统计。
2. build_subset对已纳入link补映射target普通目录及完整祖先、link父完整祖先直到BENCH_PARENT，目录去重父先子后，明确避免link_path被同时登记普通目录。不能为链接补整个release内容。
   普通空目录合法且需要创建。源target若是链接，只有依赖闭合到许可普通目标且预算不变时纳入，否则排除并写原因；未知类型排除/阻塞，不造“普通目录”。
3. inspect_plan写入前审计子集所有links的目标目录/依赖与父链；完整验收增加已纳入链接目标实际存在且类型正确的检查。悬空target必须验收false，即使linktag/target字面匹配。不要全局follow树递归统计。
   沿用同一正式执行链，在一个小fixture测试空目录junction目标实际创建后可打开；移除目标时预检或验收明确失败。测试应覆盖实际生成器目录清单，而非手写正确列表掩盖bug。
4. C上重建同一代表子集并更新真实计数/SHA、code_digest、FALSE合同(run/code/plan全部绑定)、RUNBOOK/BENCH_PLAN/manifest。
   尽量保持现有5032实体与约1GiB内容选择规则，仅修目录闭合；若新增目录/链接排除导致数量变化准确说明。仍唯一内容<=1073741824；无需再扩大类别或加中断测试。
5. 当前test_r9_capability_pilot断言旧NORMAL不存在是旧环境断言，不删除旧试验目录来让测试通过；本轮不必为此引入新的实盘试验。必要时修测试隔离，与迁移实现分开注明。
6. 本轮只C修改/构建/针对性测试，E不创建BENCH目录、不执行真实复制；不改源、不查密码/断会话，不额外全盘扫描。
   Source范围/当前一致性缺口仍保留到正式开工核验，不用这次目录修复冒称全源已确认。

## 交付
agents/chatgpt/inbox/R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014/
ZHANGWEI_REPORT.md、DIRECTORY_CLOSURE_AUDIT.json、实际修改代码/固定依赖引用、针对性测试/结果、新SUBSET_MANIFEST、更新FALSE合同与RUNBOOK/BENCH_PLAN、FILE_SHA256（不含自哈希）。
小库或真实子集目录闭合审计摘要足以审核；不必上传整个来源大计划。报告明确合法统一入口已实现、当前唯一目录闭合缺口是否修完，不能重复只交“以后再接线”。
完成HOLD_PENDING_CODE_REVIEW；审完下一轮只发这一次代表性实盘测速，不加新微型场景。
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
执行电脑=ZHANGWEI；SAM=HOLD。更新INBOX_FOR_CHATGPT.md。
