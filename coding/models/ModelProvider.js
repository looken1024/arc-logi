"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BaseModel = void 0;
class BaseModel {
    constructor(config) {
        this.config = config;
    }
    validateConfig() {
        if (!this.config.apiKey) {
            throw new Error('API key is required');
        }
        if (!this.config.modelName) {
            throw new Error('Model name is required');
        }
    }
}
exports.BaseModel = BaseModel;
//# sourceMappingURL=ModelProvider.js.map