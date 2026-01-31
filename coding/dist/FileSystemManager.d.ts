/// <reference types="node" />
import * as fs from 'fs';
export interface FileOperation {
    type: 'create' | 'update' | 'delete' | 'rename';
    path: string;
    content?: string;
    newPath?: string;
    timestamp: Date;
}
export declare class FileSystemManager {
    private workspaceRoot;
    private operations;
    constructor(workspaceRoot?: string);
    setWorkspace(root: string): void;
    getWorkspace(): string;
    createFile(filePath: string, content?: string): Promise<void>;
    readFile(filePath: string): Promise<string>;
    updateFile(filePath: string, content: string): Promise<void>;
    deleteFile(filePath: string): Promise<void>;
    renameFile(oldPath: string, newPath: string): Promise<void>;
    listFiles(directory?: string, pattern?: RegExp): string[];
    fileExists(filePath: string): boolean;
    getFileStats(filePath: string): fs.Stats;
    getOperations(): FileOperation[];
    clearOperations(): void;
    private resolvePath;
    private ensureDirectoryExists;
    private readDirectoryRecursive;
    private recordOperation;
}
//# sourceMappingURL=FileSystemManager.d.ts.map