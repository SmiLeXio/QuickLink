import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

const projectRoot = path.resolve(process.cwd());
const distDir = path.join(projectRoot, "dist");
const distIndex = path.join(distDir, "index.html");

function run(command, args, { inheritStdio = true } = {}) {
	const result = spawnSync(command, args, {
		stdio: inheritStdio ? "inherit" : "pipe",
		shell: false,
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

function resolveDeployBase(env) {
	const explicit = process.env.DEPLOY_BASE;
	if (explicit) return explicit;
	if (env === "test") return "/opt/homepage-test";
	if (env === "dev") return "/opt/homepage-dev";
	return "/opt/homepage";
}

function requireDist() {
	if (!existsSync(distDir)) {
		throw new Error(`dist 不存在：${distDir}。请先运行 npm run build`);
	}
	if (!existsSync(distIndex)) {
		throw new Error(`dist/index.html 不存在：${distIndex}。请先运行 npm run build`);
	}
}

const host = getArgValue("--host") ?? process.env.DEPLOY_HOST ?? "taoserver";
const env = getArgValue("--env") ?? process.env.DEPLOY_ENV ?? "prod";
const deployBase = resolveDeployBase(env);
const remoteDist = `${deployBase}/dist`;
const remoteUpload = `${deployBase}/_upload/dist.new`;

requireDist();

run("ssh", ["-o", "BatchMode=yes", host, `bash -lc "set -euo pipefail; mkdir -p '${remoteDist}' '${remoteUpload}'"`]);
run("scp", ["-r", "dist/.", `${host}:${remoteUpload}/`]);
run("ssh", [
	"-o",
	"BatchMode=yes",
	host,
	`bash -lc "set -euo pipefail; command -v rsync >/dev/null 2>&1 || (apt-get update -y && apt-get install -y rsync); rsync -a --delete '${remoteUpload}/' '${remoteDist}/'; rm -rf '${remoteUpload}'"`,
]);

run("ssh", [
	"-o",
	"BatchMode=yes",
	host,
	`bash -lc "set -euo pipefail; curl -I -sS --max-time 5 http://127.0.0.1/ | head -n 1 || true"`,
]);

const publicIp = process.env.DEPLOY_PUBLIC_IP ?? "123.57.134.105";
process.stdout.write(`\n发布完成：\n- 公网：http://${publicIp}/（需放行安全组 TCP 80）\n- 隧道：ssh -L 8080:127.0.0.1:80 ${host}  然后访问 http://localhost:8080/\n`);
