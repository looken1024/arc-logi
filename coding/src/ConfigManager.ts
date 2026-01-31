import * as fs from 'fs';
import * as path from 'path';
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

export class ConfigManager {
  private configPath: string;
  private config: AppConfig;

  constructor(configDir: string = process.cwd()) {
    this.configPath = path.join(configDir, '.aicoding-config.json');
    this.config = this.loadDefaultConfig();
    this.loadConfig();
  }

  private loadDefaultConfig(): AppConfig {
    return {
      defaultModel: {
        type: ModelType.OPENAI,
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

  loadConfig(): void {
    try {
      if (fs.existsSync(this.configPath)) {
        const configData = fs.readFileSync(this.configPath, 'utf-8');
        this.config = { ...this.config, ...JSON.parse(configData) };
      }
    } catch (error: any) {
      console.warn('Failed to load config file, using defaults:', error.message);
    }
  }

  saveConfig(): void {
    try {
      const configDir = path.dirname(this.configPath);
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      
      fs.writeFileSync(this.configPath, JSON.stringify(this.config, null, 2), 'utf-8');
    } catch (error: any) {
      console.error('Failed to save config:', error.message);
    }
  }

  getConfig(): AppConfig {
    return { ...this.config };
  }

  updateConfig(updates: Partial<AppConfig>): void {
    this.config = { ...this.config, ...updates };
    this.saveConfig();
  }

  getModelConfig(): { type: ModelType; config: ModelConfig } {
    return { ...this.config.defaultModel };
  }

  setModelConfig(type: ModelType, config: ModelConfig): void {
    this.config.defaultModel = { type, config };
    this.saveConfig();
  }

  getWorkspace(): string {
    return this.config.workspace;
  }

  setWorkspace(workspace: string): void {
    this.config.workspace = workspace;
    this.saveConfig();
  }

  getPreferences() {
    return { ...this.config.preferences };
  }

  setPreferences(preferences: Partial<AppConfig['preferences']>): void {
    this.config.preferences = { ...this.config.preferences, ...preferences };
    this.saveConfig();
  }

  resetToDefaults(): void {
    this.config = this.loadDefaultConfig();
    this.saveConfig();
  }

  configExists(): boolean {
    return fs.existsSync(this.configPath);
  }

  getConfigPath(): string {
    return this.configPath;
  }
}