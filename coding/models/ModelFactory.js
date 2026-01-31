"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ModelFactory = exports.ModelType = void 0;
const OpenAIModel_1 = require("./OpenAIModel");
const GeminiModel_1 = require("./GeminiModel");
const DeepSeekModel_1 = require("./DeepSeekModel");
var ModelType;
(function (ModelType) {
    ModelType["OPENAI"] = "openai";
    ModelType["GEMINI"] = "gemini";
    ModelType["DEEPSEEK"] = "deepseek";
})(ModelType = exports.ModelType || (exports.ModelType = {}));
class ModelFactory {
    static createModel(type, config) {
        switch (type) {
            case ModelType.OPENAI:
                return new OpenAIModel_1.OpenAIModel(config);
            case ModelType.GEMINI:
                return new GeminiModel_1.GeminiModel(config);
            case ModelType.DEEPSEEK:
                return new DeepSeekModel_1.DeepSeekModel(config);
            default:
                throw new Error(`Unsupported model type: ${type}`);
        }
    }
    static detectModelType(modelName) {
        if (modelName.includes('gpt')) {
            return ModelType.OPENAI;
        }
        else if (modelName.includes('gemini')) {
            return ModelType.GEMINI;
        }
        else if (modelName.includes('deepseek')) {
            return ModelType.DEEPSEEK;
        }
        throw new Error(`Cannot detect model type from name: ${modelName}`);
    }
    static getAvailableModels() {
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
exports.ModelFactory = ModelFactory;
//# sourceMappingURL=ModelFactory.js.map