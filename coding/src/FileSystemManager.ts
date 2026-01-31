import * as fs from 'fs';
import * as path from 'path';

export interface FileOperation {
  type: 'create' | 'update' | 'delete' | 'rename';
  path: string;
  content?: string;
  newPath?: string;
  timestamp: Date;
}

export class FileSystemManager {
  private workspaceRoot: string;
  private operations: FileOperation[] = [];

  constructor(workspaceRoot: string = process.cwd()) {
    this.workspaceRoot = workspaceRoot;
  }

  setWorkspace(root: string): void {
    if (!fs.existsSync(root)) {
      throw new Error(`Workspace directory does not exist: ${root}`);
    }
    this.workspaceRoot = root;
  }

  getWorkspace(): string {
    return this.workspaceRoot;
  }

  async createFile(filePath: string, content: string = ''): Promise<void> {
    const fullPath = this.resolvePath(filePath);
    this.ensureDirectoryExists(path.dirname(fullPath));
    
    await fs.promises.writeFile(fullPath, content, 'utf-8');
    this.recordOperation('create', filePath, content);
  }

  async readFile(filePath: string): Promise<string> {
    const fullPath = this.resolvePath(filePath);
    
    if (!fs.existsSync(fullPath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    return await fs.promises.readFile(fullPath, 'utf-8');
  }

  async updateFile(filePath: string, content: string): Promise<void> {
    const fullPath = this.resolvePath(filePath);
    
    if (!fs.existsSync(fullPath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    await fs.promises.writeFile(fullPath, content, 'utf-8');
    this.recordOperation('update', filePath, content);
  }

  async deleteFile(filePath: string): Promise<void> {
    const fullPath = this.resolvePath(filePath);
    
    if (!fs.existsSync(fullPath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    await fs.promises.unlink(fullPath);
    this.recordOperation('delete', filePath);
  }

  async renameFile(oldPath: string, newPath: string): Promise<void> {
    const oldFullPath = this.resolvePath(oldPath);
    const newFullPath = this.resolvePath(newPath);
    
    if (!fs.existsSync(oldFullPath)) {
      throw new Error(`File not found: ${oldPath}`);
    }

    this.ensureDirectoryExists(path.dirname(newFullPath));
    await fs.promises.rename(oldFullPath, newFullPath);
    this.recordOperation('rename', oldPath, undefined, newPath);
  }

  listFiles(directory: string = '.', pattern?: RegExp): string[] {
    const fullPath = this.resolvePath(directory);
    
    if (!fs.existsSync(fullPath)) {
      throw new Error(`Directory not found: ${directory}`);
    }

    const files: string[] = [];
    this.readDirectoryRecursive(fullPath, files, pattern);
    
    return files.map(file => path.relative(this.workspaceRoot, file));
  }

  fileExists(filePath: string): boolean {
    return fs.existsSync(this.resolvePath(filePath));
  }

  getFileStats(filePath: string): fs.Stats {
    return fs.statSync(this.resolvePath(filePath));
  }

  getOperations(): FileOperation[] {
    return [...this.operations];
  }

  clearOperations(): void {
    this.operations = [];
  }

  private resolvePath(relativePath: string): string {
    return path.resolve(this.workspaceRoot, relativePath);
  }

  private ensureDirectoryExists(dirPath: string): void {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }

  private readDirectoryRecursive(currentPath: string, results: string[], pattern?: RegExp): void {
    const items = fs.readdirSync(currentPath);
    
    for (const item of items) {
      const fullPath = path.join(currentPath, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        this.readDirectoryRecursive(fullPath, results, pattern);
      } else if (stat.isFile()) {
        if (!pattern || pattern.test(item)) {
          results.push(fullPath);
        }
      }
    }
  }

  private recordOperation(
    type: FileOperation['type'], 
    filePath: string, 
    content?: string,
    newPath?: string
  ): void {
    const operation: FileOperation = {
      type,
      path: filePath,
      content: content || '',
      newPath: newPath || '',
      timestamp: new Date()
    };
    this.operations.push(operation);
  }
}