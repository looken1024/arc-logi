"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfigManager = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const ModelFactory_1 = require("../models/ModelFactory");
class ConfigManager {
    constructor(configDir = process.cwd()) {
        this.configPath = path.join(configDir, '.aicoding.config.json');
        this.config = this.loadDefaultConfig();
        this.loadConfig();
    }
    loadDefaultConfig() {
        return {
            defaultModel: {
                type: ModelFactory_1.ModelType.OPENAI,
                config: {
                    apiKey: '',
                    modelName: 'gpt-4',
                    temperature: 0.7,
                    maxTokens: 2000
                }
            },
            workspace: process.cwd(),
            preferences: {
                codeStyle: 'commented',
                includeTests: false,
                includeDocs: true,
                autoSave: true
            }
        };
    }
    loadConfig() {
        try {
            if (fs.existsSync(this.configPath)) {
                const configData = fs.readFileSync(this.configPath, 'utf-8');
                this.config = { ...this.config, ...JSON.parse(configData) };
            }
        }
        catch (error) {
            console.warn('Failed to load config file, using defaults:', error.message);
        }
    }
    saveConfig() {
        try {
            const configDir = path.dirname(this.configPath);
            if (!fs.existsSync(configDir)) {
                fs.mkdirSync(configDir, { recursive: true });
            }
            fs.writeFileSync(this.configPath, JSON.stringify(this.config, null, 2), 'utf-8');
        }
        catch (error) {
            console.error('Failed to save config:', error.message);
        }
    }
    getConfig() {
        return { ...this.config };
    }
    updateConfig(updates) {
        this.config = { ...this.config, ...updates };
        this.saveConfig();
    }
    getModelConfig() {
        return { ...this.config.defaultModel };
    }
    setModelConfig(type, config) {
        this.config.defaultModel = { type, config };
        this.saveConfig();
    }
    getWorkspace() {
        return this.config.workspace;
    }
    setWorkspace(workspace) {
        this.config.workspace = workspace;
        this.saveConfig();
    }
    getPreferences() {
        return { ...this.config.preferences };
    }
    setPreferences(preferences) {
        this.config.preferences = { ...this.config.preferences, ...preferences };
        this.saveConfig();
    }
    resetToDefaults() {
        this.config = this.loadDefaultConfig();
        this.saveConfig();
    }
    configExists() {
        return fs.existsSync(this.configPath);
    }
    getConfigPath() {
        return this.configPath;
    }
}
exports.ConfigManager = ConfigManager;
//# sourceMappingURL=ConfigManager.js.map