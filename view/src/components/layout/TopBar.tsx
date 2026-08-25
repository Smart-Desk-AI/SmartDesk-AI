'use client';

import { useProject } from '@/context/ProjectContext';
import styles from './TopBar.module.css';

interface TopBarProps {
  title: string;
  subtitle?: string;
}

export default function TopBar({ title, subtitle }: TopBarProps) {
  const { projectId, setProjectId } = useProject();

  return (
    <header className={styles.topbar}>
      <div className={styles.left}>
        <h1 className={styles.title}>{title}</h1>
        {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
      </div>

      <div className={styles.right}>
        <div className={styles.projectSelector}>
          <label htmlFor="project-id-input" className={styles.projectLabel}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
            Project ID
          </label>
          <input
            id="project-id-input"
            type="number"
            min={1}
            value={projectId}
            onChange={(e) => {
              const v = parseInt(e.target.value, 10);
              if (v > 0) setProjectId(v);
            }}
            className={styles.projectInput}
          />
        </div>
      </div>
    </header>
  );
}
