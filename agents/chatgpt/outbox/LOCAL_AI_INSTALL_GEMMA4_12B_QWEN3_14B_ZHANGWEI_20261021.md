# ZHANGWEI | 安装两款本地模型（用户最终确认）
task_id: LOCAL_AI_INSTALL_GEMMA4_12B_QWEN3_14B_ZHANGWEI_20261021
execution_host: ZHANGWEI
status: NEW
priority: STANDARD_NONDISRUPTIVE
AUTHORIZED_SCOPE: INSTALL_LOCAL_RUNTIME_AND_TWO_MODELS_VALIDATE_ONLY
COPY_AUTHORIZED: false
BLACKBOX_DATA_MODIFICATION_AUTHORIZED: false
EXTRA_BILLING_AUTHORIZED: false

## 用户明确选择
用户决定安装 Google **Gemma 4 12B** 和阿里巴巴 **Qwen3 14B**；不要误装 Gemini 在线 API、不要误装 Qwen3.5 9B、不要改成 Qwen3.5 14B。
台式机配置已知 Ryzen 9950X / RTX 5080 16GB / RAM 128GB；台式机 D 盘约 1TB 可用。独立目录 D:\LOCAL_AI，**不得放到 BLACKBOX 数据根目录，也不能影响正在运行的只读盘点 Worker**。

精确 Ollama tags：
- `gemma4:12b-it-q4_K_M`（Google Gemma 4 12B，视觉+文字，官方 Ollama 8GB 左右）
- `qwen3:14b-q4_K_M`（Qwen3 14B，文字模型，官方 Ollama 9.3GB 左右）
官方出处：
https://ollama.com/library/gemma4/tags
https://ollama.com/library/qwen3/tags
https://docs.ollama.com/windows

## 安装与配置
1. 首先在本机**只读**检查：D 磁盘剩余空间、Ollama 是否已安装/运行、NVIDIA 驱动与 GPU 能否被 Ollama 识别、模型是否已存在，现有后台业务 CPU/RAM/GPU 负载；不盲目重新安装或覆盖已有运行环境。
2. Ollama 若未安装，下载验证官方 Windows 安装程序，使用官方支持的 `OllamaSetup.exe /DIR="D:\LOCAL_AI\Ollama"` 安装；不要运行未知来源脚本，不开启云端付费 API。已有 Ollama 版本正常时优先保留，只调整存储目录；若需升级，先报告对现有进程的影响。
3. 设置当前用户 `OLLAMA_MODELS=D:\LOCAL_AI\Models`，使模型数据确实落 D 盘；更新环境变量后按官方说明重启 Ollama 进程并验证生效。创建独立 D:\LOCAL_AI\Watchdog 与 D:\LOCAL_AI\Logs 供**未来**窗口通知程序使用，不在本安装任务擅自实现新的 GUI 控制或自动发送 GPT。
4. 顺序拉取上述**精确两个 tags**，每个下载结束检查 `ollama list`、模型存储路径与体积。必须记录最终模型 tag、hash/digest/量化格式、运行环境版本。
5. **顺序推理验证，不要同时把两款常驻显存**。Gemma 4：本机生成一个无敏感信息测试截图，验证能真正接受图片并给出准确的界面状态描述；Qwen3 14B：验证中文任务分类和结构化输出，不宣称可以直接看图。每项需给实际输出，不以模型可下载当作模型可运行。
6. 以 8K-16K 的上下文作为后续视觉通讯测试的起点，实际显存限制以测试数据为准。记录每款单独加载时的 GPU 显存、加载与首响应耗时、卸载后显存释放状况（Ollama keep_alive 控制）。不能误把硬盘体积当运行显存占用。
7. 不动现有 Cursor/Grok 模型配置、不改网络、HUB、R9、BLACKBOX 数据、权限或账号凭据。当前业务查验长任务若正在运行，不因下载/测试中断。GPU 资源紧张则低优先级/推迟推理验证，不擅停 Worker。
8. 如安装器需要新增管理员权限、来源无法验证或明显影响正在运行的业务，暂停该风险步骤并回报，不自称安装完毕。

## 验收报告
发布至 `agents/chatgpt/inbox/LOCAL_AI_INSTALL_GEMMA4_12B_QWEN3_14B_ZHANGWEI_20261021/REPORT.md` 和 `STATUS.json`：
- HOST/INSTALL_PATH/OLLAMA_MODELS/OLLAMA_VERSION
- GEMMA4_MODEL_TAG/DIGEST/INSTALL_STATUS/VISION_INPUT_TEST
- QWEN3_MODEL_TAG/DIGEST/INSTALL_STATUS/TEXT_OUTPUT_TEST
- GPU_DETECTED/VRAM_PEAK_PER_MODEL/UNLOAD_TEST
- PREEXISTING_BLACKBOX_WORKER_UNAFFECTED / REMAINING_BLOCKER
- 具体失败原因和所需用户动作；未验证标 UNVERIFIED，不能写 PASS。

本轮仅完成两个模型的真正本地安装及独立能力验收。下一任务才搭建“两窗口查收 HUB 通知员”，避免把安装测试与 GUI 自动化未验证功能混为一谈。
