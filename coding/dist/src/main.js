#!/usr/bin/env node
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AICodingTool = void 0;
const CLIProcessor_1 = require("./CLIProcessor");
const ConfigManager_1 = require("./ConfigManager");
class AICodingTool {
    constructor() {
        this.config = new ConfigManager_1.ConfigManager();
        this.cli = new CLIProcessor_1.CLIProcessor();
    }
    async run() {
        const args = process.argv.slice(2);
        if (args.length === 0) {
            // Interactive mode
            await this.cli.startInteractive();
        }
        else {
            // Command line mode
            const result = await this.cli.processInput(args.join(' '));
            if (result) {
                console.log(result);
            }
        }
    }
    async initialize() {
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
exports.AICodingTool = AICodingTool;
// Main execution
async function main() {
    try {
        const app = new AICodingTool();
        await app.initialize();
        await app.run();
    }
    catch (error) {
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
