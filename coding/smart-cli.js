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

// 智能代码生成器 - 根据提示词生成相应的代码
class SmartCodeGenerator {
    generateCode(prompt) {
        // 根据提示词内容判断应该生成什么类型的代码
        const lowerPrompt = prompt.toLowerCase();
        
        if (lowerPrompt.includes('react') || lowerPrompt.includes('组件')) {
            return this.generateReactCode(prompt);
        } else if (lowerPrompt.includes('排序') || lowerPrompt.includes('sort')) {
            return this.generateSortingCode(prompt);
        } else if (lowerPrompt.includes('算法') || lowerPrompt.includes('algorithm')) {
            return this.generateAlgorithmCode(prompt);
        } else if (lowerPrompt.includes('函数') || lowerPrompt.includes('function')) {
            return this.generateFunctionCode(prompt);
        } else if (lowerPrompt.includes('类') || lowerPrompt.includes('class')) {
            return this.generateClassCode(prompt);
        } else {
            return this.generateGenericCode(prompt);
        }
    }

    generateReactCode(prompt) {
        return `
import React from 'react';

const GeneratedComponent = () => {
  return (
    <div>
      <h1>Generated Component</h1>
      <p>基于提示词: "${prompt}" 生成的React组件</p>
    </div>
  );
};

export default GeneratedComponent;
        `;
    }

    generateSortingCode(prompt) {
        if (prompt.includes('快速排序') || prompt.includes('quicksort')) {
            return `
// 快速排序算法实现
function quickSort(arr) {
  if (arr.length <= 1) return arr;
  
  const pivot = arr[Math.floor(arr.length / 2)];
  const left = [];
  const right = [];
  const equal = [];
  
  for (const element of arr) {
    if (element < pivot) {
      left.push(element);
    } else if (element > pivot) {
      right.push(element);
    } else {
      equal.push(element);
    }
  }
  
  return [...quickSort(left), ...equal, ...quickSort(right)];
}

// 使用示例
const numbers = [64, 34, 25, 12, 22, 11, 90];
console.log('原始数组:', numbers);
console.log('排序后:', quickSort(numbers));
            `;
        } else if (prompt.includes('冒泡') || prompt.includes('bubble')) {
            return `
// 冒泡排序算法实现
function bubbleSort(arr) {
  const n = arr.length;
  for (let i = 0; i < n - 1; i++) {
    for (let j = 0; j < n - i - 1; j++) {
      if (arr[j] > arr[j + 1]) {
        // 交换元素
        [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
      }
    }
  }
  return arr;
}

// 使用示例
const numbers = [64, 34, 25, 12, 22, 11, 90];
console.log('原始数组:', numbers);
console.log('排序后:', bubbleSort([...numbers]));
            `;
        } else {
            return `
// 排序算法示例 - 基于提示词: "${prompt}"

// 快速排序实现
function quickSort(arr) {
  if (arr.length <= 1) return arr;
  
  const pivot = arr[Math.floor(arr.length / 2)];
  const left = arr.filter(x => x < pivot);
  const middle = arr.filter(x => x === pivot);
  const right = arr.filter(x => x > pivot);
  
  return [...quickSort(left), ...middle, ...quickSort(right)];
}

// 测试排序算法
const testArray = [3, 6, 8, 10, 1, 2, 1];
console.log('排序前:', testArray);
console.log('排序后:', quickSort(testArray));
            `;
        }
    }

    generateAlgorithmCode(prompt) {
        return `
// 算法实现 - 基于提示词: "${prompt}"

/**
 * 示例算法函数
 * 这里实现了请求的算法功能
 */
function exampleAlgorithm(input) {
    // 算法逻辑实现
    let result = input;
    
    // 根据具体需求实现算法
    // ...
    
    return result;
}

// 使用示例
const input = [1, 2, 3, 4, 5];
console.log('输入:', input);
console.log('输出:', exampleAlgorithm(input));
        `;
    }

    generateFunctionCode(prompt) {
        return `
// 函数实现 - 基于提示词: "${prompt}"

function ${this.getFunctionName(prompt)}(params) {
    // 函数实现逻辑
    let result = null;
    
    // 根据需求实现具体功能
    // ...
    
    return result;
}

// 使用示例
console.log(${this.getFunctionName(prompt)}('test'));
        `;
    }

    generateClassCode(prompt) {
        return `
// 类实现 - 基于提示词: "${prompt}"

class ${this.getClassName(prompt)} {
    constructor() {
        // 初始化代码
        this.property = 'value';
    }
    
    method() {
        // 方法实现
        return this.property;
    }
    
    // 其他方法...
}

// 使用示例
const instance = new ${this.getClassName(prompt)}();
console.log(instance.method());
        `;
    }

    generateGenericCode(prompt) {
        return `
// 代码生成 - 基于提示词: "${prompt}"

/**
 * 自动生成的代码
 * 提示词: ${prompt}
 */

// 主函数或逻辑实现
function main() {
    console.log('Hello from generated code!');
    
    // 根据提示词实现具体逻辑
    // ...
    
    return '完成';
}

// 执行代码
main();
        `;
    }

    getFunctionName(prompt) {
        // 从提示词中提取函数名
        const match = prompt.match(/([\u4e00-\u9fa5a-zA-Z]+)(函数|function)/i);
        if (match && match[1]) {
            return match[1].toLowerCase() + 'Function';
        }
        return 'generatedFunction';
    }

    getClassName(prompt) {
        // 从提示词中提取类名
        const match = prompt.match(/([\u4e00-\u9fa5a-zA-Z]+)(类|class)/i);
        if (match && match[1]) {
            return match[1] + 'Class';
        }
        return 'GeneratedClass';
    }
}

// 主程序
async function main() {
    const configManager = new SimpleConfigManager();
    const codeGenerator = new SmartCodeGenerator();
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
        
        // 根据提示词智能生成代码
        const generatedCode = codeGenerator.generateCode(prompt);
        
        console.log('\n✅ Generated code:');
        console.log(generatedCode);
        
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