import type { ComponentSpec, CodeFile } from './types';

export class ComponentGenerator {
  public createComponent(spec: ComponentSpec): CodeFile {
    const componentContent = this.generateComponentContent(spec);
    const componentPath = `src/components/${spec.name}.tsx`;

    return {
      path: componentPath,
      content: componentContent,
    };
  }

  private generateComponentContent(spec: ComponentSpec): string {
    const propsInterface = `interface ${spec.name}Props {\n${
      Object.entries(spec.props)
        .map(([propName, propType]) => `  ${propName}: ${propType};`)
        .join('\n')
    }\n}`;

    const stateInterface = `interface ${spec.name}State {\n${
      Object.entries(spec.state)
        .map(([stateName, stateType]) => `  ${stateName}: ${stateType};`)
        .join('\n')
    }\n}`;

    const children = spec.children.map(child => `<${child.name} />`).join('\n    ');

    return `
import React, { useState } from 'react';
${spec.children.map(child => `import ${child.name} from './${child.name}';`).join('\n')}

${propsInterface}

${stateInterface}

const ${spec.name}: React.FC<${spec.name}Props> = (props) => {
  const [state, setState] = useState<${spec.name}State>({
    ${Object.keys(spec.state).map(stateName => `${stateName}: ''`).join(',\n    ')}
  });

  return (
    <div>
      {/* Component content goes here */}
      ${children}
    </div>
  );
};

export default ${spec.name};
`;
  }
}