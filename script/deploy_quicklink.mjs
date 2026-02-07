import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// 获取当前脚本所在目录的绝对路径
const __dirname = path.dirname(fileURLToPath(import.meta.url));
// 项目根目录 (假设脚本在 script/ 目录下)
const projectRoot = path.resolve(__dirname, "..");

const frontendDir = path.join(projectRoot, "frontend");
const frontendDist = path.join(frontendDir, "dist");
const backendDir = path.join(projectRoot, "backend");

function run(command, args, { inheritStdio = true, cwd = projectRoot } = {}) {
    console.log(`> ${command} ${args.join(" ")}`);
    // Windows 下执行 npm 需要 shell: true
    const useShell = process.platform === "win32" && (command === "npm" || command === "npm.cmd");
    const result = spawnSync(command, args, {
        stdio: inheritStdio ? "inherit" : "pipe",
        shell: useShell,
        cwd: cwd
    });
    if (result.error) throw result.error;
    if (result.status !== 0) {
        throw new Error(`Command failed: ${command} ${args.join(" ")}`);
    }
    return result;
}

function getArgValue(flag) {
    const index = process.argv.indexOf(flag);
    if (index < 0) return undefined;
    return process.argv[index + 1];
}

// 配置
const host = getArgValue("--host") ?? process.env.DEPLOY_HOST ?? "taoserver";
const deployBase = "/opt/quicklink"; // 专门为 QuickLink 设置的部署目录
const remoteDist = `${deployBase}/dist`;
const remoteBackend = `${deployBase}/backend`;
const remoteUpload = `${deployBase}/_upload`;

console.log(">>> 开始部署 QuickLink...");
console.log(`>>> 目标服务器: ${host}`);
console.log(`>>> 部署路径: ${deployBase}`);

// 1. 构建前端
console.log("\n>>> [1/5] 构建前端...");
if (!existsSync(frontendDir)) {
    throw new Error(`Frontend directory not found: ${frontendDir}`);
}
// 安装前端依赖 (可选，如果已经安装可以跳过，这里为了保险起见)
if (!existsSync(path.join(frontendDir, "node_modules"))) {
    run("npm", ["install"], { cwd: frontendDir });
}
run("npm", ["run", "build"], { cwd: frontendDir });

if (!existsSync(frontendDist)) {
    throw new Error(`Build failed, dist not found: ${frontendDist}`);
}

// 2. 准备远程目录
console.log("\n>>> [2/5] 准备远程目录...");
run("ssh", ["-o", "BatchMode=yes", host, `bash -lc "set -euo pipefail; mkdir -p '${remoteDist}' '${remoteBackend}' '${remoteUpload}'"`]);

// 3. 上传前端文件
console.log("\n>>> [3/5] 上传前端文件...");
// 确保目标父目录存在
run("ssh", ["-o", "BatchMode=yes", host, `mkdir -p ${remoteUpload}/dist_new`]);

run("scp", ["-r", `${frontendDist}/.`, `${host}:${remoteUpload}/dist_new/`]);
// 使用 rsync 或 mv 替换旧文件
run("ssh", [
    "-o", "BatchMode=yes", host,
    `bash -lc "set -euo pipefail; rm -rf '${remoteDist}/*'; cp -r '${remoteUpload}/dist_new/.' '${remoteDist}/'; rm -rf '${remoteUpload}/dist_new'"`
]);

// 4. 上传后端文件
console.log("\n>>> [4/5] 上传后端文件...");
// 排除 venv 和 __pycache__
// 注意: scp 没有 exclude 选项，这里简单起见上传整个文件夹，建议在服务器端处理忽略，或者使用 rsync
// 如果本地有 rsync，优先使用 rsync
try {
    console.log("    尝试使用 rsync 上传后端 (排除 venv, __pycache__, *.db)...");
    run("rsync", [
        "-avz",
        "--exclude", "venv",
        "--exclude", "__pycache__",
        "--exclude", ".git",
        "--exclude", "*.db",
        `${backendDir}/`,
        `${host}:${remoteBackend}/`
    ]);
} catch (e) {
    console.log("    rsync 失败或未安装，回退到 scp (可能会上传不必要的文件)...");
    run("ssh", ["-o", "BatchMode=yes", host, `mkdir -p ${remoteUpload}/backend_new`]);
    run("scp", ["-r", `${backendDir}/.`, `${host}:${remoteUpload}/backend_new/`]);
    // 在覆盖之前删除上传的 .db 文件，防止覆盖服务器上的数据库
    run("ssh", [
        "-o", "BatchMode=yes", host,
        `bash -lc "set -euo pipefail; find '${remoteUpload}/backend_new' -name '*.db' -delete; cp -r '${remoteUpload}/backend_new/.' '${remoteBackend}/'; rm -rf '${remoteUpload}/backend_new'"`
    ]);
}

// 5. 远程执行后续操作 (依赖安装 & 重启服务)
console.log("\n>>> [5/5] 更新服务器环境 & 重启服务...");
const remoteScript = `
set -e
echo "Checking Python environment..."
cd ${remoteBackend}
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || {
        echo "Error: Failed to create venv. Trying to install python3-venv..."
        if [ -x "$(command -v apt-get)" ]; then
             sudo apt-get update && sudo apt-get install -y python3-venv
             python3 -m venv venv
        else
             echo "Cannot install python3-venv automatically. Please install it manually."
             exit 1
        fi
    }
fi
echo "Installing/Updating requirements..."
# 确保 pip 已安装 (有些 venv 默认不带 pip)
if [ ! -f "venv/bin/pip" ]; then
    echo "pip not found in venv. Installing pip..."
    if [ -x "$(command -v apt-get)" ]; then
         sudo apt-get update && sudo apt-get install -y python3-pip
    fi
    # 尝试使用 ensurepip
    ./venv/bin/python3 -m ensurepip --upgrade || true
    # 如果 ensurepip 失败，尝试手动下载 get-pip.py (备选方案)
    if [ ! -f "venv/bin/pip" ]; then
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        ./venv/bin/python3 get-pip.py
        rm get-pip.py
    fi
fi

./venv/bin/pip install -r requirements.txt

echo "Restarting Systemd service..."
# 尝试重启服务，如果服务不存在则发出警告
if systemctl list-units --full -all | grep -q "quicklink.service"; then
    sudo systemctl restart quicklink
    echo "Service restarted."
else
    echo "WARNING: quicklink.service not found. Please run setup_server.sh on the server first."
fi
`;

run("ssh", [
    "-o", "BatchMode=yes", host,
    `bash -lc "${remoteScript.replace(/"/g, '\\"')}"`
]);

console.log("\n>>> 部署完成!");
console.log(`- 前端: http://${host}/quicklink/ (取决于 Nginx 配置)`);
console.log(`- 后端: http://${host}/api/`);
