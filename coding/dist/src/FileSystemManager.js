"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.FileSystemManager = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class FileSystemManager {
    constructor(workspaceRoot = process.cwd()) {
        this.operations = [];
        this.workspaceRoot = workspaceRoot;
    }
    setWorkspace(root) {
        if (!fs.existsSync(root)) {
            throw new Error(`Workspace directory does not exist: ${root}`);
        }
        this.workspaceRoot = root;
    }
    getWorkspace() {
        return this.workspaceRoot;
    }
    async createFile(filePath, content = '') {
        const fullPath = this.resolvePath(filePath);
        this.ensureDirectoryExists(path.dirname(fullPath));
        await fs.promises.writeFile(fullPath, content, 'utf-8');
        this.recordOperation('create', filePath, content);
    }
    async readFile(filePath) {
        const fullPath = this.resolvePath(filePath);
        if (!fs.existsSync(fullPath)) {
            throw new Error(`File not found: ${filePath}`);
        }
        return await fs.promises.readFile(fullPath, 'utf-8');
    }
    async updateFile(filePath, content) {
        const fullPath = this.resolvePath(filePath);
        if (!fs.existsSync(fullPath)) {
            throw new Error(`File not found: ${filePath}`);
        }
        await fs.promises.writeFile(fullPath, content, 'utf-8');
        this.recordOperation('update', filePath, content);
    }
    async deleteFile(filePath) {
        const fullPath = this.resolvePath(filePath);
        if (!fs.existsSync(fullPath)) {
            throw new Error(`File not found: ${filePath}`);
        }
        await fs.promises.unlink(fullPath);
        this.recordOperation('delete', filePath);
    }
    async renameFile(oldPath, newPath) {
        const oldFullPath = this.resolvePath(oldPath);
        const newFullPath = this.resolvePath(newPath);
        if (!fs.existsSync(oldFullPath)) {
            throw new Error(`File not found: ${oldPath}`);
        }
        this.ensureDirectoryExists(path.dirname(newFullPath));
        await fs.promises.rename(oldFullPath, newFullPath);
        this.recordOperation('rename', oldPath, undefined, newPath);
    }
    listFiles(directory = '.', pattern) {
        const fullPath = this.resolvePath(directory);
        if (!fs.existsSync(fullPath)) {
            throw new Error(`Directory not found: ${directory}`);
        }
        const files = [];
        this.readDirectoryRecursive(fullPath, files, pattern);
        return files.map(file => path.relative(this.workspaceRoot, file));
    }
    fileExists(filePath) {
        return fs.existsSync(this.resolvePath(filePath));
    }
    getFileStats(filePath) {
        return fs.statSync(this.resolvePath(filePath));
    }
    getOperations() {
        return [...this.operations];
    }
    clearOperations() {
        this.operations = [];
    }
    resolvePath(relativePath) {
        return path.resolve(this.workspaceRoot, relativePath);
    }
    ensureDirectoryExists(dirPath) {
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
        }
    }
    readDirectoryRecursive(currentPath, results, pattern) {
        const items = fs.readdirSync(currentPath);
        for (const item of items) {
            const fullPath = path.join(currentPath, item);
            const stat = fs.statSync(fullPath);
            if (stat.isDirectory()) {
                this.readDirectoryRecursive(fullPath, results, pattern);
            }
            else if (stat.isFile()) {
                if (!pattern || pattern.test(item)) {
                    results.push(fullPath);
                }
            }
        }
    }
    recordOperation(type, filePath, content, newPath) {
        const operation = {
            type,
            path: filePath,
            content: content || '',
            newPath: newPath || '',
            timestamp: new Date()
        };
        this.operations.push(operation);
    }
}
exports.FileSystemManager = FileSystemManager;
