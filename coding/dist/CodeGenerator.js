"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CodeGenerator = void 0;
const ModelFactory_1 = require("../models/ModelFactory");
class CodeGenerator {
    constructor(modelType, config) {
        this.model = ModelFactory_1.ModelFactory.createModel(modelType, config);
    }
    async generateFile(prompt, fileName, options = {}) {
        const context = this.buildGenerationContext(fileName, options);
        return await this.model.generateCode(prompt, context);
    }
    async generateComponent(componentName, componentType, options = {}) {
        const prompt = `Create a ${componentType} component named ${componentName}`;
        const context = this.buildComponentContext(componentType, options);
        return await this.model.generateCode(prompt, context);
    }
    async analyzeCode(code, fileName) {
        const analysis = await this.model.analyzeCode(code, `Analyze this code from ${fileName} for quality, issues, and suggestions`);
        // Parse the analysis result into structured format
        return this.parseAnalysisResult(analysis);
    }
    async refactorCode(code, fileName, goal) {
        const prompt = `Refactor the following code to ${goal}. Provide only the refactored code without explanations.`;
        const context = `Original code from ${fileName}:\n\`\`\`\n${code}\n\`\`\``;
        return await this.model.generateCode(prompt, context);
    }
    buildGenerationContext(fileName, options) {
        const parts = [
            `File: ${fileName}`,
            options.language ? `Language: ${options.language}` : '',
            options.framework ? `Framework: ${options.framework}` : '',
            options.style ? `Code style: ${options.style}` : '',
            options.includeTests ? 'Include unit tests' : '',
            options.includeDocs ? 'Include documentation comments' : ''
        ];
        return parts.filter(Boolean).join('\n');
    }
    buildComponentContext(componentType, options) {
        const baseContext = this.buildGenerationContext(`Component.${this.getFileExtension(componentType)}`, options);
        const componentSpecific = {
            react: 'Use functional components with hooks, modern React patterns',
            vue: 'Use Composition API with script setup, modern Vue 3 patterns',
            angular: 'Use standalone components, modern Angular patterns',
            svelte: 'Use Svelte 4+ patterns with modern syntax'
        }[componentType];
        return `${baseContext}\n${componentSpecific}`;
    }
    getFileExtension(componentType) {
        const extensions = {
            react: 'jsx',
            vue: 'vue',
            angular: 'ts',
            svelte: 'svelte'
        };
        return extensions[componentType] || 'js';
    }
    parseAnalysisResult(analysis) {
        // Simple parsing logic - in practice would use more sophisticated parsing
        const lines = analysis.split('\n');
        const issues = [];
        const suggestions = [];
        let quality = 80; // Default
        let complexity = 'medium';
        lines.forEach(line => {
            if (line.toLowerCase().includes('issue:') || line.toLowerCase().includes('problem:')) {
                issues.push(line.replace(/^(issue|problem):\s*/i, '').trim());
            }
            else if (line.toLowerCase().includes('suggestion:') || line.toLowerCase().includes('recommendation:')) {
                suggestions.push(line.replace(/^(suggestion|recommendation):\s*/i, '').trim());
            }
            else if (line.toLowerCase().includes('quality:')) {
                const match = line.match(/quality:\s*(\d+)/i);
                if (match && match[1])
                    quality = parseInt(match[1]);
            }
            else if (line.toLowerCase().includes('complexity:')) {
                const comp = line.toLowerCase().replace('complexity:', '').trim();
                if (['low', 'medium', 'high'].includes(comp)) {
                    complexity = comp;
                }
            }
        });
        return { quality, issues, suggestions, complexity };
    }
}
exports.CodeGenerator = CodeGenerator;
//# sourceMappingURL=CodeGenerator.js.map