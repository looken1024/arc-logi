import { ModelConfig } from '../models/ModelProvider';
import { ModelType } from '../models/ModelFactory';
export interface AppConfig {
    defaultModel: {
        type: ModelType;
        config: ModelConfig;
    };
    workspace: string;
    preferences: {
        codeStyle: 'concise' | 'detailed' | 'commented';
        includeTests: boolean;
        includeDocs: boolean;
        autoSave: boolean;
    };
}
export declare class ConfigManager {
    private configPath;
    private config;
    constructor(configDir?: string);
    private loadDefaultConfig;
    loadConfig(): void;
    saveConfig(): void;
    getConfig(): AppConfig;
    updateConfig(updates: Partial<AppConfig>): void;
    getModelConfig(): {
        type: ModelType;
        config: ModelConfig;
    };
    setModelConfig(type: ModelType, config: ModelConfig): void;
    getWorkspace(): string;
    setWorkspace(workspace: string): void;
    getPreferences(): {
        codeStyle: "concise" | "detailed" | "commented";
        includeTests: boolean;
        includeDocs: boolean;
        autoSave: boolean;
    };
    setPreferences(preferences: Partial<AppConfig['preferences']>): void;
    resetToDefaults(): void;
    configExists(): boolean;
    getConfigPath(): string;
}
//# sourceMappingURL=ConfigManager.d.ts.map