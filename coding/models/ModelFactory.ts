import { BaseModel, ModelConfig } from './ModelProvider';
import { OpenAIModel } from './OpenAIModel';
import { GeminiModel } from './GeminiModel';
import { DeepSeekModel } from './DeepSeekModel';

export enum ModelType {
  OPENAI = 'openai',
  GEMINI = 'gemini',
  DEEPSEEK = 'deepseek'
}

export class ModelFactory {
  static createModel(type: ModelType, config: ModelConfig): BaseModel {
    switch (type) {
      case ModelType.OPENAI:
        return new OpenAIModel(config);
      case ModelType.GEMINI:
        return new GeminiModel(config);
      case ModelType.DEEPSEEK:
        return new DeepSeekModel(config);
      default:
        throw new Error(`Unsupported model type: ${type}`);
    }
  }

  static detectModelType(modelName: string): ModelType {
    if (modelName.includes('gpt')) {
      return ModelType.OPENAI;
    } else if (modelName.includes('gemini')) {
      return ModelType.GEMINI;
    } else if (modelName.includes('deepseek')) {
      return ModelType.DEEPSEEK;
    }
    throw new Error(`Cannot detect model type from name: ${modelName}`);
  }

  static getAvailableModels(): { type: ModelType; name: string; description: string }[] {
    return [
      {
        type: ModelType.OPENAI,
        name: 'GPT-4',
        description: 'OpenAI\'s most capable model'
      },
      {
        type: ModelType.OPENAI,
        name: 'GPT-3.5-turbo',
        description: 'OpenAI\'s fast and cost-effective model'
      },
      {
        type: ModelType.GEMINI,
        name: 'gemini-pro',
        description: 'Google\'s Gemini Pro model'
      },
      {
        type: ModelType.DEEPSEEK,
        name: 'deepseek-coder',
        description: 'DeepSeek\'s code-specific model'
      }
    ];
  }
}