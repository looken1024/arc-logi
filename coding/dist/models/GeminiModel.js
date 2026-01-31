"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GeminiModel = void 0;
const ModelProvider_1 = require("./ModelProvider");
class GeminiModel extends ModelProvider_1.BaseModel {
    constructor(config) {
        super(config);
        this.apiBaseURL = config.baseURL || 'https://generativelanguage.googleapis.com/v1beta';
        this.validateConfig();
    }
    async chat(messages) {
        // Convert to Gemini format
        const contents = messages.map(msg => ({
            role: msg.role === 'assistant' ? 'model' : 'user',
            parts: [{ text: msg.content }]
        }));
        const response = await fetch(`${this.apiBaseURL}/models/${this.config.modelName}:generateContent?key=${this.config.apiKey}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                contents: contents,
                generationConfig: {
                    temperature: this.config.temperature || 0.7,
                    maxOutputTokens: this.config.maxTokens || 2000
                }
            })
        });
        if (!response.ok) {
            throw new Error(`Gemini API error: ${response.statusText}`);
        }
        const data = await response.json();
        return {
            content: data.candidates[0].content.parts[0].text,
            usage: data.usageMetadata ? {
                promptTokens: data.usageMetadata.promptTokenCount,
                completionTokens: data.usageMetadata.candidatesTokenCount,
                totalTokens: data.usageMetadata.totalTokenCount
            } : undefined
        };
    }
    async generateCode(prompt, context) {
        const messages = [
            {
                role: 'user',
                content: `You are an expert software developer. Generate clean, efficient, and well-documented code.\n\n${context ? `Context: ${context}\n\n` : ''}Task: ${prompt}`
            }
        ];
        const response = await this.chat(messages);
        return response.content;
    }
    async analyzeCode(code, task) {
        const messages = [
            {
                role: 'user',
                content: `You are a code review expert. Analyze the provided code and provide constructive feedback.\n\nCode to analyze:\n\`\`\`\n${code}\n\`\`\`\n\nTask: ${task}`
            }
        ];
        const response = await this.chat(messages);
        return response.content;
    }
}
exports.GeminiModel = GeminiModel;
