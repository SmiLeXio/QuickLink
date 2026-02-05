import { spawnSync } from "node:child_process";
import { writeFileSync, unlinkSync } from "node:fs";

// 配置
function getArgValue(flag) {
    const index = process.argv.indexOf(flag);
    if (index < 0) return undefined;
    return process.argv[index + 1];
}

const host = getArgValue("--host") ?? process.env.DEPLOY_HOST ?? "taoserver";
const deployBase = "/opt/quicklink";
const serviceName = "quicklink.service";

function run(command, args, { inheritStdio = true, shell = true } = {}) {
    console.log(`> ${command} ${args.join(" ")}`);
    const result = spawnSync(command, args, {
        stdio: inheritStdio ? "inherit" : "pipe",
        shell: shell
    });
    if (result.error) throw result.error;
    if (result.status !== 0) {
        throw new Error(`Command failed: ${command} ${args.join(" ")}`);
    }
    return result;
}

const serviceFileContent = `[Unit]
Description=QuickLink Backend Service
After=network.target

[Service]
User=root
WorkingDirectory=${deployBase}/backend
ExecStart=${deployBase}/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
`;

const nginxConfigContent = `
    # QuickLink Config
    location /quicklink/ {
        alias ${deployBase}/dist/;
        try_files $uri $uri/ /quicklink/index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
`;

console.log(">>> 初始化 QuickLink 服务器配置...");
console.log(`>>> 目标服务器: ${host}`);

// 1. 创建 Systemd 服务文件
console.log("\n>>> [1/2] 配置 Systemd 服务...");

try {
    // 写入本地临时文件
    writeFileSync("quicklink.service", serviceFileContent);

    // 上传文件
    console.log("正在上传服务文件...");
    run("scp", ["quicklink.service", `${host}:/tmp/quicklink.service`], { shell: false });

    // 移动文件并重启服务
    console.log("正在配置并重启服务...");
    const remoteCmd = `sudo mv /tmp/quicklink.service /etc/systemd/system/${serviceName} && sudo systemctl daemon-reload && sudo systemctl enable ${serviceName} && sudo systemctl restart ${serviceName}`;
    run("ssh", ["-o", "BatchMode=yes", host, remoteCmd], { shell: false });

    console.log("Systemd 服务配置成功并已启动！");
} catch (e) {
    console.error("配置 Systemd 服务失败，请检查 sudo 权限或 SSH 连接。");
    throw e;
} finally {
    try { unlinkSync("quicklink.service"); } catch (e) { }
}

// 2. 打印 Nginx 配置
console.log("\n>>> [2/2] Nginx 配置指南");
console.log("========================================================");
console.log("请登录服务器，将以下内容添加到 Nginx 配置文件中 (通常在 /etc/nginx/sites-available/default):");
console.log("注意: 请将其粘贴到现有的 server { ... } 块内部");
console.log("========================================================");
console.log(nginxConfigContent);
console.log("========================================================");
console.log("添加完成后，请运行: sudo nginx -t && sudo systemctl restart nginx");
