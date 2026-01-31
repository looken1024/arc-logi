#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// 简单的配置文件检查
const configPath = path.join(process.cwd(), '.aicoding-config.json');

if (!fs.existsSync(configPath)) {
    console.log('🚀 AI Coding Tool Initializing...');
    console.log('📋 First-time setup required');
    console.log('Please run: aicoding init <model_type> <api_key>');
    console.log('Example: aicoding init openai your_api_key_here');
    process.exit(1);
}

// 读取配置
const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
console.log('✅ Using', config.defaultModel.type, 'model:', config.defaultModel.config.modelName);

// 处理命令行参数
const args = process.argv.slice(2);

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
    console.log('📝 This would call the DeepSeek API with your prompt...');
    
    // 模拟API响应
    const reactCode = `
import React from 'react';

const HelloWorld = () => {
  return (
    <div>
      <h1>Hello World!</h1>
      <p>这是一个React函数组件示例</p>
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