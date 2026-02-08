import React from 'react'
import { DocsThemeConfig } from 'nextra-theme-docs'

const config: DocsThemeConfig = {
  logo: <span><strong>KidneyAI</strong></span>,
  project: {
    link: 'https://github.com/shuding/nextra-docs-template',
  },
  docsRepositoryBase: 'https://github.com/shuding/nextra-docs-template',
  footer: {
    content: (
      <span>
        BMES Hackathon 2026 - Kidney Allocation Optimization
      </span>
    )
  }
}

export default config
