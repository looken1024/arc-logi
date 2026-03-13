# 修改说明：增强opencode输出显示

为了解决用户在执行opencode远程调用时输出不完整的问题，我对admin服务进行了以下修改：

## 问题分析
用户反馈在执行opencode命令时，有些内容（尤其是思考过程）没有完全显示在前端，导致以为命令卡住了。

## 解决方案
在Flask应用中添加环境变量以强制启用彩色输出，因为：
1. 许多命令行工具（包括opencode）会根据终端能力决定是否输出ANSI颜色代码
2. 当输出被重定向到管道或文件时，这些工具可能会禁用彩色输出
3. 前端已经实现了ANSI到HTML的转换函数(ansiToHtml)，可以正确显示彩色输出

## 具体修改
在 `/home/yangkai/github/arc-logi/admin/app.py` 中：

1. 在 `execute_command()` 函数中添加：
   ```python
   env = os.environ.copy()
   env['TERM'] = 'xterm-256color'
   env['FORCE_COLOR'] = '1'
   result = subprocess.run(
       ['bash', '-i', '-c', command],
       cwd=workdir,
       capture_output=True,
       text=True,
       timeout=300,
       env=env
   )
   ```

2. 在 `execute_command_stream()` 函数中同样添加相同的环境变量设置

## 期望效果
- opencode及其子进程将强制输出ANSI颜色代码
- 前端的ansiToHtml函数将正确转换这些代码为HTML样式
- 用户应该能看到opencode完整的输出，包括思考过程和执行结果
- 减少因输出不完整而误以为命令卡住的情况

## 服务重启
修改后已通过 `./ctl.sh restart` 重启服务以应用更改。

## 注意事项
- 这些更改仅影响admin服务的命令执行行为
- 不会影响其他功能
- 如果用户仍然遇到问题，可能需要检查opencode自身的输出缓冲或日志设置