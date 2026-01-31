#!/usr/bin/env node

// 稳定的代码生成器 - 专门处理常见提示词
class StableCodeGenerator {
    generateCode(prompt) {
        const lowerPrompt = prompt.toLowerCase();
        
        // 精确匹配常见需求
        if (lowerPrompt.includes('快速排序') || lowerPrompt.includes('quicksort')) {
            return this.generateQuickSort();
        } else if (lowerPrompt.includes('冒泡排序') || lowerPrompt.includes('bubble')) {
            return this.generateBubbleSort();
        } else if (lowerPrompt.includes('计数器') && lowerPrompt.includes('react')) {
            return this.generateReactCounter();
        } else if (lowerPrompt.includes('react') && lowerPrompt.includes('组件')) {
            return this.generateReactComponent(prompt);
        } else if (lowerPrompt.includes('排序算法')) {
            return this.generateSortingAlgorithms();
        } else {
            return this.generateGenericCode(prompt);
        }
    }

    generateQuickSort() {
        return `// 快速排序算法实现
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

// 测试示例
const numbers = [64, 34, 25, 12, 22, 11, 90];
console.log('原始数组:', numbers);
console.log('排序后:', quickSort(numbers));`;
    }

    generateReactCounter() {
        return `import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <h1>计数器: {count}</h1>
      <button onClick={() => setCount(count + 1)}>+1</button>
      <button onClick={() => setCount(count - 1)}>-1</button>
      <button onClick={() => setCount(0)}>重置</button>
    </div>
  );
}

export default Counter;`;
    }

    generateBubbleSort() {
        return `// 冒泡排序算法实现
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

// 测试示例
const numbers = [64, 34, 25, 12, 22, 11, 90];
console.log('原始数组:', numbers);
console.log('排序后:', bubbleSort([...numbers]));`;
    }

    generateSortingAlgorithms() {
        return `// 多种排序算法实现

// 1. 快速排序
function quickSort(arr) {
  if (arr.length <= 1) return arr;
  const pivot = arr[Math.floor(arr.length / 2)];
  const left = arr.filter(x => x < pivot);
  const middle = arr.filter(x => x === pivot);
  const right = arr.filter(x => x > pivot);
  return [...quickSort(left), ...middle, ...quickSort(right)];
}

// 2. 冒泡排序
function bubbleSort(arr) {
  const n = arr.length;
  for (let i = 0; i < n - 1; i++) {
    for (let j = 0; j < n - i - 1; j++) {
      if (arr[j] > arr[j + 1]) {
        [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
      }
    }
  }
  return arr;
}

// 3. 选择排序
function selectionSort(arr) {
  const n = arr.length;
  for (let i = 0; i < n - 1; i++) {
    let minIndex = i;
    for (let j = i + 1; j < n; j++) {
      if (arr[j] < arr[minIndex]) {
        minIndex = j;
      }
    }
    [arr[i], arr[minIndex]] = [arr[minIndex], arr[i]];
  }
  return arr;
}

// 测试所有排序算法
const testArray = [64, 34, 25, 12, 22, 11, 90];
console.log('原始数组:', testArray);
console.log('快速排序:', quickSort([...testArray]));
console.log('冒泡排序:', bubbleSort([...testArray]));
console.log('选择排序:', selectionSort([...testArray]));`;
    }

    generateReactComponent(prompt) {
        return `import React from 'react';

function MyComponent() {
  return (
    <div>
      <h1>React组件</h1>
      <p>基于提示词"${prompt}"生成的组件</p>
    </div>
  );
}

export default MyComponent;`;
    }

    generateGenericCode(prompt) {
        return `// 生成的代码 - 基于提示词: "${prompt}"

function main() {
  console.log('开始执行代码');
  
  // 在这里实现您的需求
  // 根据提示词添加相应的功能
  
  console.log('代码执行完成');
  return 'success';
}

// 执行代码
const result = main();
console.log('结果:', result);`;
    }
}

// 主程序
function main() {
    const codeGenerator = new StableCodeGenerator();
    const args = process.argv.slice(2);

    if (args.length === 0) {
        console.log('使用方法: node stable-cli.js generate "你的提示词"');
        console.log('示例: node stable-cli.js generate "快速排序算法"');
        return;
    }

    const command = args[0];

    if (command === 'generate' && args.length > 1) {
        const prompt = args.slice(1).join(' ');
        console.log('生成代码，提示词:', prompt);
        
        try {
            const generatedCode = codeGenerator.generateCode(prompt);
            console.log('\n生成的代码:');
            console.log(generatedCode);
        } catch (error) {
            console.log('生成代码时出错:', error.message);
        }
        
    } else {
        console.log('未知命令:', command);
        console.log('使用方法: node stable-cli.js generate "你的提示词"');
    }
}

// 运行程序
main();