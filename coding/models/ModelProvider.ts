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

export abstract class BaseModel {
  protected config: ModelConfig;

  constructor(config: ModelConfig) {
    this.config = config;
  }

  abstract chat(messages: ChatMessage[]): Promise<ModelResponse>;
  
  abstract generateCode(prompt: string, context?: string): Promise<string>;
  
  abstract analyzeCode(code: string, task: string): Promise<string>;

  protected validateConfig(): void {
    if (!this.config.apiKey) {
      throw new Error('API key is required');
    }
    if (!this.config.modelName) {
      throw new Error('Model name is required');
    }
  }
}