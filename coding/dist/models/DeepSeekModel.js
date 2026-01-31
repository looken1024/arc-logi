"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DeepSeekModel = void 0;
const ModelProvider_1 = require("./ModelProvider");
class DeepSeekModel extends ModelProvider_1.BaseModel {
    constructor(config) {
        super(config);
        this.apiBaseURL = config.baseURL || 'https://api.deepseek.com/v1';
        this.validateConfig();
    }
    async chat(messages) {
        const response = await fetch(`${this.apiBaseURL}/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.config.apiKey}`
            },
            body: JSON.stringify({
                model: this.config.modelName,
                messages: messages,
                temperature: this.config.temperature || 0.7,
                max_tokens: this.config.maxTokens || 2000
            })
        });
        if (!response.ok) {
            throw new Error(`DeepSeek API error: ${response.statusText}`);
        }
        const data = await response.json();
        return {
            content: data.choices[0].message.content,
            usage: data.usage ? {
                promptTokens: data.usage.prompt_tokens,
                completionTokens: data.usage.completion_tokens,
                totalTokens: data.usage.total_tokens
            } : undefined
        };
    }
    async generateCode(prompt, context) {
        const messages = [
            {
                role: 'system',
                content: 'You are an expert software developer. Generate clean, efficient, and well-documented code.'
            },
            {
                role: 'user',
                content: context ? `${context}\n\n${prompt}` : prompt
            }
        ];
        const response = await this.chat(messages);
        return response.content;
    }
    async analyzeCode(code, task) {
        const messages = [
            {
                role: 'system',
                content: 'You are a code review expert. Analyze the provided code and provide constructive feedback.'
            },
            {
                role: 'user',
                content: `Code to analyze:\n\`\`\`\n${code}\n\`\`\`\n\nTask: ${task}`
            }
        ];
        const response = await this.chat(messages);
        return response.content;
    }
}
exports.DeepSeekModel = DeepSeekModel;
