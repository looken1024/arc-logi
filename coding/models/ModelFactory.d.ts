import { BaseModel, ModelConfig } from './ModelProvider';
export declare enum ModelType {
    OPENAI = "openai",
    GEMINI = "gemini",
    DEEPSEEK = "deepseek"
}
export declare class ModelFactory {
    static createModel(type: ModelType, config: ModelConfig): BaseModel;
    static detectModelType(modelName: string): ModelType;
    static getAvailableModels(): {
        type: ModelType;
        name: string;
        description: string;
    }[];
}
//# sourceMappingURL=ModelFactory.d.ts.map