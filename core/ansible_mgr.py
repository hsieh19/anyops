import asyncio
import os
import shutil

# Try importing ansible_runner, which fails on native Windows due to missing 'fcntl'
try:
    import ansible_runner
    HAS_ANSIBLE = True
except ImportError:
    HAS_ANSIBLE = False

async def run_playbook_async(playbook_name: str, target_ip: str, extra_vars: dict = None):
    """
    Asynchronously executes an Ansible playbook using ansible-runner.
    If run on an environment without ansible (like native Windows), it will gracefully degrade.
    """
    # Check if ansible-playbook exists in PATH or ansible_runner import failed
    if not HAS_ANSIBLE or not shutil.which("ansible-playbook"):
        return {
            "status": "failed",
            "message": "Ansible 未在当前系统中安装。(提示: 请在打包好的 Docker 容器内执行，或在 Linux 子系统中运行此操作)"
        }
        
    private_data_dir = os.path.abspath("ansible")
    
    # We wrap the blocking ansible_runner call inside a thread so FastAPI is not blocked
    def _run_sync():
        return ansible_runner.run(
            private_data_dir=private_data_dir,
            playbook=f"playbooks/{playbook_name}",
            extravars=extra_vars or {},
            limit=target_ip, # Run only on specific IP
            quiet=True # Suppress stdout flooding
        )

    try:
        runner = await asyncio.to_thread(_run_sync)
        if runner.status == 'successful':
            return {"status": "success", "message": "任务执行完成"}
        else:
            return {"status": "failed", "message": f"任务失败，退出码: {runner.rc}"}
    except Exception as e:
        return {"status": "failed", "message": f"执行异常: {str(e)}"}
