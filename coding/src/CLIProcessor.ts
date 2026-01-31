import * as readline from 'readline';
import { CodeGenerator, CodeGenerationOptions } from './CodeGenerator';
import { FileSystemManager } from './FileSystemManager';
import { ModelFactory, ModelType } from '../models/ModelFactory';
import { ModelConfig } from '../models/ModelProvider';

export interface Command {
  name: string;
  description: string;
  usage: string;
  execute: (args: string[]) => Promise<string>;
}

export class CLIProcessor {
  private commands: Map<string, Command> = new Map();
  private codeGenerator?: CodeGenerator;
  private fileSystem: FileSystemManager;
  private rl: readline.Interface;

  constructor() {
    this.fileSystem = new FileSystemManager();
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    this.initializeCommands();
  }

  private initializeCommands(): void {
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

  registerCommand(command: Command): void {
    this.commands.set(command.name, command);
  }

  async processInput(input: string): Promise<string> {
    const [command, ...args] = input.trim().split(' ');
    
    if (!command) return '';

    const cmd = this.commands.get(command);
    if (!cmd) {
      return `Unknown command: ${command}. Type 'help' for available commands.`;
    }

    try {
      return await cmd.execute(args);
    } catch (error) {
      return `Error executing command '${command}': ${error.message}`;
    }
  }

  async startInteractive(): Promise<void> {
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

  private async initModel(args: string[]): Promise<string> {
    if (args.length < 2) {
      return 'Usage: init <model_type> <api_key> [model_name]';
    }

    const modelType = args[0] as ModelType;
    const apiKey = args[1];
    const modelName = args[2] || this.getDefaultModelName(modelType);

    const config: ModelConfig = {
      apiKey,
      modelName,
      temperature: 0.7,
      maxTokens: 2000
    };

    this.codeGenerator = new CodeGenerator(modelType, config);
    return `Initialized ${modelType} model with ${modelName}`;
  }

  private async generateCode(args: string[]): Promise<string> {
    if (!this.codeGenerator) {
      return 'Please initialize a model first with \'init\' command';
    }

    if (args.length === 0) {
      return 'Usage: generate <prompt> [--file <filename>] [--lang <language>]';
    }

    const options: CodeGenerationOptions = {};
    let prompt = '';
    let outputFile: string | null = null;

    for (let i = 0; i < args.length; i++) {
      if (args[i] === '--file' && i + 1 < args.length) {
        outputFile = args[++i];
      } else if (args[i] === '--lang' && i + 1 < args.length) {
        options.language = args[++i];
      } else if (args[i] === '--framework' && i + 1 < args.length) {
        options.framework = args[++i];
      } else {
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

  private async analyzeCode(args: string[]): Promise<string> {
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

  private async refactorCode(args: string[]): Promise<string> {
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

  private async listFiles(args: string[]): Promise<string> {
    const directory = args[0] || '.';
    const files = this.fileSystem.listFiles(directory);
    
    if (files.length === 0) {
      return `No files found in ${directory}`;
    }

    return `Files in ${directory}:\n${files.join('\n')}`;
  }

  private async showHelp(args: string[]): Promise<string> {
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

  private async listModels(_args: string[]): Promise<string> {
    const models = ModelFactory.getAvailableModels();
    let result = 'Available AI models:\n\n';
    
    models.forEach(model => {
      result += `${model.type}.${model.name.padEnd(15)} - ${model.description}\n`;
    });
    
    return result;
  }

  private getDefaultModelName(modelType: ModelType): string {
    const defaults = {
      [ModelType.OPENAI]: 'gpt-4',
      [ModelType.GEMINI]: 'gemini-pro',
      [ModelType.DEEPSEEK]: 'deepseek-coder'
    };
    
    return defaults[modelType];
  }
}