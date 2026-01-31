import { BaseModel, ModelConfig } from '../models/ModelProvider';
import { ModelFactory, ModelType } from '../models/ModelFactory';

export interface CodeGenerationOptions {
  language?: string;
  framework?: string;
  style?: 'concise' | 'detailed' | 'commented';
  includeTests?: boolean;
  includeDocs?: boolean;
}

export interface CodeAnalysisResult {
  quality: number; // 0-100
  issues: string[];
  suggestions: string[];
  complexity: 'low' | 'medium' | 'high';
}

export class CodeGenerator {
  private model: BaseModel;

  constructor(modelType: ModelType, config: ModelConfig) {
    this.model = ModelFactory.createModel(modelType, config);
  }

  async generateFile(
    prompt: string,
    fileName: string,
    options: CodeGenerationOptions = {}
  ): Promise<string> {
    const context = this.buildGenerationContext(fileName, options);
    return await this.model.generateCode(prompt, context);
  }

  async generateComponent(
    componentName: string,
    componentType: 'react' | 'vue' | 'angular' | 'svelte',
    options: CodeGenerationOptions = {}
  ): Promise<string> {
    const prompt = `Create a ${componentType} component named ${componentName}`;
    const context = this.buildComponentContext(componentType, options);
    return await this.model.generateCode(prompt, context);
  }

  async analyzeCode(code: string, fileName: string): Promise<CodeAnalysisResult> {
    const analysis = await this.model.analyzeCode(
      code,
      `Analyze this code from ${fileName} for quality, issues, and suggestions`
    );

    // Parse the analysis result into structured format
    return this.parseAnalysisResult(analysis);
  }

  async refactorCode(
    code: string,
    fileName: string,
    goal: string
  ): Promise<string> {
    const prompt = `Refactor the following code to ${goal}. Provide only the refactored code without explanations.`;
    const context = `Original code from ${fileName}:\n\`\`\`\n${code}\n\`\`\``;
    
    return await this.model.generateCode(prompt, context);
  }

  private buildGenerationContext(fileName: string, options: CodeGenerationOptions): string {
    const parts: string[] = [
      `File: ${fileName}`,
      options.language ? `Language: ${options.language}` : '',
      options.framework ? `Framework: ${options.framework}` : '',
      options.style ? `Code style: ${options.style}` : '',
      options.includeTests ? 'Include unit tests' : '',
      options.includeDocs ? 'Include documentation comments' : ''
    ];

    return parts.filter(Boolean).join('\n');
  }

  private buildComponentContext(componentType: string, options: CodeGenerationOptions): string {
    const baseContext = this.buildGenerationContext(`Component.${this.getFileExtension(componentType)}`, options);
    
    const componentSpecific = {
      react: 'Use functional components with hooks, modern React patterns',
      vue: 'Use Composition API with script setup, modern Vue 3 patterns',
      angular: 'Use standalone components, modern Angular patterns',
      svelte: 'Use Svelte 4+ patterns with modern syntax'
    }[componentType];

    return `${baseContext}\n${componentSpecific}`;
  }

  private getFileExtension(componentType: string): string {
    const extensions: Record<string, string> = {
      react: 'jsx',
      vue: 'vue',
      angular: 'ts',
      svelte: 'svelte'
    };
    return extensions[componentType] || 'js';
  }

  private parseAnalysisResult(analysis: string): CodeAnalysisResult {
    // Simple parsing logic - in practice would use more sophisticated parsing
    const lines = analysis.split('\n');
    const issues: string[] = [];
    const suggestions: string[] = [];
    let quality = 80; // Default
    let complexity: 'low' | 'medium' | 'high' = 'medium';

    lines.forEach(line => {
      if (line.toLowerCase().includes('issue:') || line.toLowerCase().includes('problem:')) {
        issues.push(line.replace(/^(issue|problem):\s*/i, '').trim());
      } else if (line.toLowerCase().includes('suggestion:') || line.toLowerCase().includes('recommendation:')) {
        suggestions.push(line.replace(/^(suggestion|recommendation):\s*/i, '').trim());
      } else if (line.toLowerCase().includes('quality:')) {
        const match = line.match(/quality:\s*(\d+)/i);
        if (match && match[1]) quality = parseInt(match[1]);
      } else if (line.toLowerCase().includes('complexity:')) {
        const comp = line.toLowerCase().replace('complexity:', '').trim();
        if (['low', 'medium', 'high'].includes(comp)) {
          complexity = comp as 'low' | 'medium' | 'high';
        }
      }
    });

    return { quality, issues, suggestions, complexity };
  }
}