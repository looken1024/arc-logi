export interface Command {
    name: string;
    description: string;
    usage: string;
    execute: (args: string[]) => Promise<string>;
}
export declare class CLIProcessor {
    private commands;
    private codeGenerator?;
    private fileSystem;
    private rl;
    constructor();
    private initializeCommands;
    registerCommand(command: Command): void;
    processInput(input: string): Promise<string>;
    startInteractive(): Promise<void>;
    private initModel;
    private generateCode;
    private analyzeCode;
    private refactorCode;
    private listFiles;
    private showHelp;
    private listModels;
    private getDefaultModelName;
}
//# sourceMappingURL=CLIProcessor.d.ts.map