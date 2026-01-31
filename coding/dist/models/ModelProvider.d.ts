export interface ModelConfig {
    apiKey: string;
    baseURL?: string;
    modelName: string;
    temperature?: number;
    maxTokens?: number;
}
export interface ChatMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}
export interface ModelResponse {
    content: string;
    usage?: {
        promptTokens: number;
        completionTokens: number;
        totalTokens: number;
    };
}
export declare abstract class BaseModel {
    protected config: ModelConfig;
    constructor(config: ModelConfig);
    abstract chat(messages: ChatMessage[]): Promise<ModelResponse>;
    abstract generateCode(prompt: string, context?: string): Promise<string>;
    abstract analyzeCode(code: string, task: string): Promise<string>;
    protected validateConfig(): void;
}
//# sourceMappingURL=ModelProvider.d.ts.map