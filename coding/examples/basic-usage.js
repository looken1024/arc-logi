// Example usage of AI Coding Tool
// This file demonstrates how to use the tool programmatically

const { AICodingTool } = require('../dist/main');

async function demonstrate() {
  console.log('🤖 AI Coding Tool Demonstration');
  console.log('==============================');
  
  // Initialize the tool
  const tool = new AICodingTool();
  
  // Example 1: Generate a simple function
  console.log('\n1. Generating a simple function:');
  const functionCode = await tool.generateCode(
    'Create a function that calculates factorial',
    'math.js'
  );
  console.log('Generated code:', functionCode);
  
  // Example 2: Analyze existing code
  console.log('\n2. Analyzing code quality:');
  const analysis = await tool.analyzeCode(
    'function test() { return 1; }',
    'test.js'
  );
  console.log('Analysis result:', analysis);
  
  // Example 3: Refactor code
  console.log('\n3. Refactoring code:');
  const refactored = await tool.refactorCode(
    'function old() { var x = 1; return x; }',
    'old.js',
    'use modern JavaScript syntax'
  );
  console.log('Refactored code:', refactored);
}

demonstrate().catch(console.error);