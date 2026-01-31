#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// 简单的配置管理器
class SimpleConfigManager {
    constructor() {
        this.configPath = path.join(process.cwd(), '.aicoding-config.json');
    }

    configExists() {
        return fs.existsSync(this.configPath);
    }

    loadConfig() {
        if (this.configExists()) {
            return JSON.parse(fs.readFileSync(this.configPath, 'utf-8'));
        }
        return null;
    }

    saveConfig(config) {
        fs.writeFileSync(this.configPath, JSON.stringify(config, null, 2), 'utf-8');
    }
}

// 主程序
async function main() {
    const configManager = new SimpleConfigManager();
    const args = process.argv.slice(2);

    // 初始化命令
    if (args[0] === 'init' && args.length >= 3) {
        const modelType = args[1];
        const apiKey = args[2];
        const modelName = args[3] || 'deepseek-coder';

        const config = {
            defaultModel: {
                type: modelType,
                config: {
                    apiKey: apiKey,
                    modelName: modelName,
                    temperature: 0.7,
                    maxTokens: 2000
                }
            },
            workspace: "./",
            preferences: {
                codeStyle: "commented",
                includeTests: false,
                includeDocs: true,
                autoSave: true
            }
        };

        configManager.saveConfig(config);
        console.log(`Initialized ${modelType} model with ${modelName}`);
        process.exit(0);
    }

    // 检查配置
    if (!configManager.configExists()) {
        console.log('🚀 AI Coding Tool Initializing...');
        console.log('📋 First-time setup required');
        console.log('Please run: aicoding init <model_type> <api_key>');
        console.log('Example: aicoding init openai your_api_key_here');
        process.exit(1);
    }

    const config = configManager.loadConfig();
    console.log('✅ Using', config.defaultModel.type, 'model:', config.defaultModel.config.modelName);

    // 其他命令处理
    if (args.length === 0) {
        console.log('\n📋 Available commands:');
        console.log('  generate <prompt>  - Generate code based on prompt');
        console.log('  init <model> <key> - Initialize with model configuration');
        console.log('  help               - Show help information');
        process.exit(0);
    }

    const command = args[0];

    if (command === 'generate' && args.length > 1) {
        const prompt = args.slice(1).join(' ');
        console.log('\n🤖 Generating code for:', prompt);
        
        // 模拟DeepSeek API调用
        const reactCode = `
import React from 'react';

const HelloWorld = () => {
  return (
    <div>
      <h1>Hello World!</h1>
      <p>这是一个使用DeepSeek生成的React函数组件</p>
    </div>
  );
};

export default HelloWorld;
        `;
        
        console.log('\n✅ Generated React component:');
        console.log(reactCode);
        
    } else if (command === 'help') {
        console.log('\n📋 AI Coding Tool Help:');
        console.log('  generate <prompt>  - Generate code based on prompt');
        console.log('  init <model> <key> - Initialize with model configuration');
        console.log('  models            - List available AI models');
        console.log('  help              - Show this help');
        
    } else {
        console.log('❌ Unknown command:', command);
        console.log('💡 Use "help" to see available commands');
        process.exit(1);
    }
}

// 运行主程序
main().catch(error => {
    console.error('❌ Error:', error.message);
    process.exit(1);
});