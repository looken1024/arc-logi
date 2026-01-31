import { ModelFactory, ModelType } from '../models/ModelFactory';
import { CodeGenerator } from '../src/CodeGenerator';
import { FileSystemManager } from '../src/FileSystemManager';

describe('AI Coding Tool Architecture', () => {
  test('ModelFactory should create models', () => {
    const config = {
      apiKey: 'test-key',
      modelName: 'test-model'
    };
    
    // Test that factory can create instances without throwing
    expect(() => {
      ModelFactory.createModel(ModelType.OPENAI, config);
    }).not.toThrow();
    
    expect(() => {
      ModelFactory.createModel(ModelType.GEMINI, config);
    }).not.toThrow();
    
    expect(() => {
      ModelFactory.createModel(ModelType.DEEPSEEK, config);
    }).not.toThrow();
  });

  test('FileSystemManager should manage files', async () => {
    const fsManager = new FileSystemManager();
    const testContent = 'console.log("Hello, World!");';
    
    // Test file creation
    await expect(fsManager.createFile('test.js', testContent)).resolves.not.toThrow();
    
    // Test file reading
    const content = await fsManager.readFile('test.js');
    expect(content).toBe(testContent);
    
    // Test file existence
    expect(fsManager.fileExists('test.js')).toBe(true);
    
    // Cleanup
    await fsManager.deleteFile('test.js');
  });

  test('CodeGenerator should have proper interface', () => {
    const config = {
      apiKey: 'test-key',
      modelName: 'test-model'
    };
    
    const generator = new CodeGenerator(ModelType.OPENAI, config);
    
    // Test that generator has required methods
    expect(generator.generateFile).toBeDefined();
    expect(generator.generateComponent).toBeDefined();
    expect(generator.analyzeCode).toBeDefined();
    expect(generator.refactorCode).toBeDefined();
  });

  test('ModelFactory should detect model types', () => {
    expect(ModelFactory.detectModelType('gpt-4')).toBe(ModelType.OPENAI);
    expect(ModelFactory.detectModelType('gemini-pro')).toBe(ModelType.GEMINI);
    expect(ModelFactory.detectModelType('deepseek-coder')).toBe(ModelType.DEEPSEEK);
  });

  test('FileSystemManager should list files', () => {
    const fsManager = new FileSystemManager();
    const files = fsManager.listFiles('.');
    
    // Should at least list the current directory
    expect(Array.isArray(files)).toBe(true);
  });
});