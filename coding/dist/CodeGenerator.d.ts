import { ModelConfig } from '../models/ModelProvider';
import { ModelType } from '../models/ModelFactory';
export interface CodeGenerationOptions {
    language?: string;
    framework?: string;
    style?: 'concise' | 'detailed' | 'commented';
    includeTests?: boolean;
    includeDocs?: boolean;
}
export interface CodeAnalysisResult {
    quality: number;
    issues: string[];
    suggestions: string[];
    complexity: 'low' | 'medium' | 'high';
}
export declare class CodeGenerator {
    private model;
    constructor(modelType: ModelType, config: ModelConfig);
    generateFile(prompt: string, fileName: string, options?: CodeGenerationOptions): Promise<string>;
    generateComponent(componentName: string, componentType: 'react' | 'vue' | 'angular' | 'svelte', options?: CodeGenerationOptions): Promise<string>;
    analyzeCode(code: string, fileName: string): Promise<CodeAnalysisResult>;
    refactorCode(code: string, fileName: string, goal: string): Promise<string>;
    private buildGenerationContext;
    private buildComponentContext;
    private getFileExtension;
    private parseAnalysisResult;
}
//# sourceMappingURL=CodeGenerator.d.ts.map