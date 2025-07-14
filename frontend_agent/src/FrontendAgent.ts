import { ComponentGenerator } from './ComponentGenerator';
import type { AgentTask, CodeArtifact } from './types';

export class FrontendAgent {
  private componentGenerator: ComponentGenerator;

  constructor() {
    this.componentGenerator = new ComponentGenerator();
  }

  public async executeTask(task: AgentTask): Promise<CodeArtifact> {
    // For now, we'll just generate a single component as a proof of concept.
    const mainComponentSpec = {
      name: 'Main',
      props: {},
      state: {},
      events: [],
      children: [],
    };

    const codeFile = this.componentGenerator.createComponent(mainComponentSpec);

    return {
      agent_type: 'FrontendAgent',
      files: {
        [codeFile.path]: codeFile.content,
      },
      dependencies: [],
      metadata: {},
    };
  }
}