export interface ComponentSpec {
  name: string;
  props: Record<string, string>;
  state: Record<string, string>;
  events: string[];
  children: ComponentSpec[];
}

export interface CodeFile {
  path: string;
  content: string;
}

export interface AgentTask {
  agent_type: string;
  description: string;
  dependencies: string[];
  priority: number;
  estimated_time: number;
}

export interface CodeArtifact {
  agent_type: string;
  files: Record<string, string>;
  dependencies: string[];
  metadata: Record<string, unknown>;
}