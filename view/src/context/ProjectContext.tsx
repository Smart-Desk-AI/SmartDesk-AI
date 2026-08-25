'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface ProjectContextValue {
  projectId: number;
  setProjectId: (id: number) => void;
}

const ProjectContext = createContext<ProjectContextValue>({
  projectId: 1,
  setProjectId: () => {},
});

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [projectId, setProjectId] = useState<number>(1);
  return (
    <ProjectContext.Provider value={{ projectId, setProjectId }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  return useContext(ProjectContext);
}
