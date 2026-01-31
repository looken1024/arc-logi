# AI Coding Tool

A powerful, extensible AI-powered coding assistant similar to Trae, supporting multiple AI models including OpenAI GPT, Google Gemini, and DeepSeek.

## 🚀 Features

- **Multi-Model Support**: Works with OpenAI GPT, Google Gemini, and DeepSeek models
- **Code Generation**: Generate code from natural language prompts
- **Code Analysis**: Analyze code quality and provide suggestions
- **Code Refactoring**: Refactor existing code with specific goals
- **File Management**: Full workspace management with file operations
- **Interactive CLI**: User-friendly command-line interface
- **Configurable**: Easy configuration for different models and preferences

## 📦 Installation

```bash
# Clone the repository
git clone <your-repo>
cd coding

# Install dependencies
npm install

# Build the project
npm run build

# Install globally (optional)
npm install -g .
```

## 🔧 Configuration

First-time setup requires configuring your AI model:

```bash
# Initialize with OpenAI
aicoding init openai your_openai_api_key

# Initialize with Gemini
aicoding init gemini your_gemini_api_key

# Initialize with DeepSeek
aicoding init deepseek your_deepseek_api_key
```

## 🎯 Usage

### Interactive Mode
```bash
aicoding
> generate Create a React component that displays a counter
> analyze src/App.js
> refactor old-code.js use modern JavaScript syntax
```

### Command Line Mode
```bash
# Generate code
aicoding generate "Create a Python function to calculate fibonacci" --file fib.py

# Analyze code
aicoding analyze src/components/Button.js

# Refactor code
aicoding refactor legacy.js "convert to ES6 modules"

# List files
aicoding list src
```

### Available Commands

- `init <model_type> <api_key>` - Initialize with AI model
- `generate <prompt>` - Generate code from prompt
- `analyze <filename>` - Analyze code quality
- `refactor <filename> <goal>` - Refactor code
- `list [directory]` - List files in workspace
- `models` - Show available AI models
- `help` - Show help information

## 🤖 Supported Models

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Google Gemini**: gemini-pro
- **DeepSeek**: deepseek-coder

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│           CLI Interface          │
├─────────────────────────────────┤
│        Command Processor        │
├─────────────────────────────────┤
│      Code Generation Engine      │
├─────────────────────────────────┤
│        Model Abstraction        │
├─────────────────────────────────┤
│   GPT   │  Gemini  │ DeepSeek   │
└─────────────────────────────────┘
```

### Core Modules

1. **Model Abstraction Layer**: Unified interface for multiple AI models
2. **CodeGenerator**: Core code generation and analysis engine
3. **FileSystemManager**: File operations and workspace management
4. **CLIProcessor**: Command parsing and interactive interface
5. **ConfigManager**: Configuration and preferences management

## 🔌 Extending with New Models

To add support for a new AI model:

1. Create a new model class extending `BaseModel`
2. Implement the required methods: `chat`, `generateCode`, `analyzeCode`
3. Register the model in `ModelFactory.ts`
4. Update configuration types if needed

Example:
```typescript
export class NewAIModel extends BaseModel {
  async chat(messages: ChatMessage[]): Promise<ModelResponse> {
    // Implement model-specific API calls
  }
}
```

## 🧪 Testing

```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## 📝 Examples

See the `examples/` directory for usage examples:

- `basic-usage.js` - Programmatic API usage
- `react-component.js` - Generating React components
- `code-analysis.js` - Code quality analysis examples

## 🔧 Development

```bash
# Development build with watch mode
npm run dev

# Production build
npm run build

# Lint code
npm run lint
```

## 📊 Performance

- **Response Time**: Typically 2-10 seconds depending on model and complexity
- **Token Usage**: Configurable with `maxTokens` setting
- **Memory**: Lightweight, minimal memory footprint

## 🛡️ Security

- API keys are stored in local configuration only
- No data is sent to external services except the configured AI model APIs
- File operations are sandboxed to the workspace directory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- Create an issue for bugs or feature requests
- Check examples for common usage patterns
- Review the architecture documentation for extension points

---

Built with ❤️ for the developer community