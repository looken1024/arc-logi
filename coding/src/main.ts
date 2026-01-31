#!/usr/bin/env node

import { CLIProcessor } from './CLIProcessor';
import { ConfigManager } from './ConfigManager';

class AICodingTool {
  private cli: CLIProcessor;
  private config: ConfigManager;

  constructor() {
    this.config = new ConfigManager();
    this.cli = new CLIProcessor();
  }

  async run(): Promise<void> {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
      // Interactive mode
      await this.cli.startInteractive();
    } else {
      // Command line mode
      const result = await this.cli.processInput(args.join(' '));
      if (result) {
        console.log(result);
      }
    }
  }

  async initialize(): Promise<void> {
    console.log('🚀 AI Coding Tool Initializing...');
    
    // Check if config exists, if not prompt for setup
    if (!this.config.configExists()) {
      console.log('📋 First-time setup required');
      console.log('Please run: aicoding init <model_type> <api_key>');
      console.log('Example: aicoding init openai your_api_key_here');
      return;
    }

    const modelConfig = this.config.getModelConfig();
    console.log(`✅ Using ${modelConfig.type} model: ${modelConfig.config.modelName}`);
  }
}

// Main execution
async function main() {
  try {
    const app = new AICodingTool();
    await app.initialize();
    await app.run();
  } catch (error: any) {
    console.error('❌ Fatal error:', error.message);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n👋 Goodbye!');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n👋 Goodbye!');
  process.exit(0);
});

// Run the application
if (require.main === module) {
  main().catch(console.error);
}

export { AICodingTool };