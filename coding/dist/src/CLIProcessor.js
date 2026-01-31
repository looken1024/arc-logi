"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.CLIProcessor = void 0;
const readline = __importStar(require("readline"));
const CodeGenerator_1 = require("./CodeGenerator");
const FileSystemManager_1 = require("./FileSystemManager");
const ModelFactory_1 = require("../models/ModelFactory");
class CLIProcessor {
    constructor() {
        this.commands = new Map();
        this.fileSystem = new FileSystemManager_1.FileSystemManager();
        this.rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });
        this.initializeCommands();
    }
    initializeCommands() {
        this.registerCommand({
            name: 'init',
            description: 'Initialize AI coding tool with model configuration',
            usage: 'init <model_type> <api_key> [model_name]',
            execute: this.initModel.bind(this)
        });
        this.registerCommand({
            name: 'generate',
            description: 'Generate code based on prompt',
            usage: 'generate <prompt> [--file <filename>] [--lang <language>]',
            execute: this.generateCode.bind(this)
        });
        this.registerCommand({
            name: 'analyze',
            description: 'Analyze code in a file',
            usage: 'analyze <filename>',
            execute: this.analyzeCode.bind(this)
        });
        this.registerCommand({
            name: 'refactor',
            description: 'Refactor code in a file',
            usage: 'refactor <filename> <goal>',
            execute: this.refactorCode.bind(this)
        });
        this.registerCommand({
            name: 'list',
            description: 'List files in workspace',
            usage: 'list [directory]',
            execute: this.listFiles.bind(this)
        });
        this.registerCommand({
            name: 'help',
            description: 'Show help information',
            usage: 'help [command]',
            execute: this.showHelp.bind(this)
        });
        this.registerCommand({
            name: 'models',
            description: 'List available AI models',
            usage: 'models',
            execute: this.listModels.bind(this)
        });
    }
    registerCommand(command) {
        this.commands.set(command.name, command);
    }
    async processInput(input) {
        const [command, ...args] = input.trim().split(' ');
        if (!command)
            return '';
        const cmd = this.commands.get(command);
        if (!cmd) {
            return `Unknown command: ${command}. Type 'help' for available commands.`;
        }
        try {
            return await cmd.execute(args);
        }
        catch (error) {
            return `Error executing command '${command}': ${error.message}`;
        }
    }
    async startInteractive() {
        console.log('AI Coding Tool - Interactive Mode');
        console.log('Type \'help\' for available commands.\n');
        const prompt = () => {
            this.rl.question('> ', async (input) => {
                if (input.toLowerCase() === 'exit' || input.toLowerCase() === 'quit') {
                    this.rl.close();
                    return;
                }
                const result = await this.processInput(input);
                if (result) {
                    console.log(result);
                }
                prompt();
            });
        };
        prompt();
    }
    async initModel(args) {
        if (args.length < 2) {
            return 'Usage: init <model_type> <api_key> [model_name]';
        }
        const modelType = args[0];
        const apiKey = args[1];
        const modelName = args[2] || this.getDefaultModelName(modelType);
        const config = {
            apiKey,
            modelName,
            temperature: 0.7,
            maxTokens: 2000
        };
        this.codeGenerator = new CodeGenerator_1.CodeGenerator(modelType, config);
        return `Initialized ${modelType} model with ${modelName}`;
    }
    async generateCode(args) {
        if (!this.codeGenerator) {
            return 'Please initialize a model first with \'init\' command';
        }
        if (args.length === 0) {
            return 'Usage: generate <prompt> [--file <filename>] [--lang <language>]';
        }
        const options = {};
        let prompt = '';
        let outputFile = null;
        for (let i = 0; i < args.length; i++) {
            if (args[i] === '--file' && i + 1 < args.length) {
                outputFile = args[++i];
            }
            else if (args[i] === '--lang' && i + 1 < args.length) {
                options.language = args[++i];
            }
            else if (args[i] === '--framework' && i + 1 < args.length) {
                options.framework = args[++i];
            }
            else {
                prompt += args[i] + ' ';
            }
        }
        prompt = prompt.trim();
        const generatedCode = await this.codeGenerator.generateFile(prompt, outputFile || 'generated.js', options);
        if (outputFile) {
            await this.fileSystem.createFile(outputFile, generatedCode);
            return `Generated and saved to ${outputFile}`;
        }
        return generatedCode;
    }
    async analyzeCode(args) {
        if (!this.codeGenerator) {
            return 'Please initialize a model first with \'init\' command';
        }
        if (args.length === 0) {
            return 'Usage: analyze <filename>';
        }
        const filename = args[0];
        const code = await this.fileSystem.readFile(filename);
        const analysis = await this.codeGenerator.analyzeCode(code, filename);
        return `Analysis for ${filename}:\n\n${analysis}`;
    }
    async refactorCode(args) {
        if (!this.codeGenerator) {
            return 'Please initialize a model first with \'init\' command';
        }
        if (args.length < 2) {
            return 'Usage: refactor <filename> <goal>';
        }
        const filename = args[0];
        const goal = args.slice(1).join(' ');
        const code = await this.fileSystem.readFile(filename);
        const refactored = await this.codeGenerator.refactorCode(code, filename, goal);
        await this.fileSystem.updateFile(filename, refactored);
        return `Refactored ${filename} to ${goal}`;
    }
    async listFiles(args) {
        const directory = args[0] || '.';
        const files = this.fileSystem.listFiles(directory);
        if (files.length === 0) {
            return `No files found in ${directory}`;
        }
        return `Files in ${directory}:\n${files.join('\n')}`;
    }
    async showHelp(args) {
        if (args.length > 0) {
            const command = this.commands.get(args[0]);
            if (!command) {
                return `Command not found: ${args[0]}`;
            }
            return `${command.name}: ${command.description}\nUsage: ${command.usage}`;
        }
        let helpText = 'Available commands:\n\n';
        this.commands.forEach(command => {
            helpText += `${command.name.padEnd(10)} - ${command.description}\n`;
        });
        helpText += '\nType \'help <command>\' for detailed usage.';
        return helpText;
    }
    async listModels(_args) {
        const models = ModelFactory_1.ModelFactory.getAvailableModels();
        let result = 'Available AI models:\n\n';
        models.forEach(model => {
            result += `${model.type}.${model.name.padEnd(15)} - ${model.description}\n`;
        });
        return result;
    }
    getDefaultModelName(modelType) {
        const defaults = {
            [ModelFactory_1.ModelType.OPENAI]: 'gpt-4',
            [ModelFactory_1.ModelType.GEMINI]: 'gemini-pro',
            [ModelFactory_1.ModelType.DEEPSEEK]: 'deepseek-coder'
        };
        return defaults[modelType];
    }
}
exports.CLIProcessor = CLIProcessor;
