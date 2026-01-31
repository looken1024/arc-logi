#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

class SimpleAICoding {
  constructor() {
    this.configFile = path.join(process.cwd(), '.aicoding-config.json');
    this.config = this.loadConfig();
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
  }

  loadConfig() {
    try {
      if (fs.existsSync(this.configFile)) {
        return JSON.parse(fs.readFileSync(this.configFile, 'utf-8'));
      }
    } catch (error) {
      // Ignore config errors
    }
    return { model: 'openai', apiKey: '' };
  }

  saveConfig() {
    try {
      fs.writeFileSync(this.configFile, JSON.stringify(this.config, null, 2));
    } catch (error) {
      console.error('Failed to save config:', error.message);
    }
  }

  async init(modelType, apiKey) {
    this.config.model = modelType;
    this.config.apiKey = apiKey;
    this.saveConfig();
    console.log(`✅ Initialized ${modelType} model`);
  }

  async processCommand(input) {
    const [command, ...args] = input.trim().split(' ');
    
    switch (command) {
      case 'init':
        if (args.length < 2) return 'Usage: init <model_type> <api_key>';
        return await this.init(args[0], args[1]);
        
      case 'generate':
        if (!this.config.apiKey) return 'Please initialize first with: init <model_type> <api_key>';
        return await this.generateCode(args.join(' '));
        
      case 'help':
        return `Available commands:
  init <model_type> <api_key> - Initialize AI model
  generate <prompt> - Generate code
  help - Show this help`;
        
      default:
        return `Unknown command: ${command}. Type 'help' for available commands.`;
    }
  }

  async generateCode(prompt) {
    console.log('🤖 Generating code...');
    
    // 模拟AI代码生成（实际使用时需要替换为真实的API调用）
    const examples = {
      'react component': 'function MyComponent() { return <div>Hello World</div>; }',
      'python function': 'def hello_world():\n    print("Hello, World!")\n    return True',
      'javascript class': 'class MyClass {\n  constructor() {\n    this.value = 42;\n  }\n  \n  getValue() {\n    return this.value;\n  }\n}'
    };
    
    // 简单的关键词匹配
    let generatedCode = '// Generated code based on your prompt\n';
    
    if (prompt.toLowerCase().includes('react')) {
      generatedCode += examples['react component'];
    } else if (prompt.toLowerCase().includes('python')) {
      generatedCode += examples['python function'];
    } else if (prompt.toLowerCase().includes('class')) {
      generatedCode += examples['javascript class'];
    } else {
      generatedCode += 'function example() {\n  // Your code here\n  return "Hello, World!";\n}';
    }
    
    return generatedCode;
  }

  async start() {
    console.log('🚀 Simple AI Coding Tool');
    console.log('Type \'help\' for available commands\n');

    const promptUser = () => {
      this.rl.question('> ', async (input) => {
        if (input.toLowerCase() === 'exit' || input.toLowerCase() === 'quit') {
          this.rl.close();
          return;
        }

        const result = await this.processCommand(input);
        console.log(result + '\n');
        
        promptUser();
      });
    };

    promptUser();
  }
}

// 命令行参数处理
if (require.main === module) {
  const tool = new SimpleAICoding();
  
  if (process.argv.length > 2) {
    // 命令行模式
    tool.processCommand(process.argv.slice(2).join(' '))
      .then(result => {
        console.log(result);
        process.exit(0);
      })
      .catch(error => {
        console.error('Error:', error.message);
        process.exit(1);
      });
  } else {
    // 交互模式
    tool.start();
  }
}

module.exports = SimpleAICoding;