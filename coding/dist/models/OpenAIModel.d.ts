import { BaseModel, ModelConfig, ChatMessage, ModelResponse } from './ModelProvider';
export declare class OpenAIModel extends BaseModel {
    private apiBaseURL;
    constructor(config: ModelConfig);
    chat(messages: ChatMessage[]): Promise<ModelResponse>;
    generateCode(prompt: string, context?: string): Promise<string>;
    analyzeCode(code: string, task: string): Promise<string>;
}
//# sourceMappingURL=OpenAIModel.d.ts.map