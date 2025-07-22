import { scriptConfigurations, type ScriptConfiguration, type InsertScriptConfiguration } from "@shared/schema";

export interface IStorage {
  createScriptConfiguration(config: InsertScriptConfiguration): Promise<ScriptConfiguration>;
  getScriptConfiguration(id: number): Promise<ScriptConfiguration | undefined>;
}

export class MemStorage implements IStorage {
  private configurations: Map<number, ScriptConfiguration>;
  currentId: number;

  constructor() {
    this.configurations = new Map();
    this.currentId = 1;
  }

  async createScriptConfiguration(insertConfig: InsertScriptConfiguration): Promise<ScriptConfiguration> {
    const id = this.currentId++;
    const config: ScriptConfiguration = { ...insertConfig, id };
    this.configurations.set(id, config);
    return config;
  }

  async getScriptConfiguration(id: number): Promise<ScriptConfiguration | undefined> {
    return this.configurations.get(id);
  }
}

export const storage = new MemStorage();
