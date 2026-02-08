import React from 'react'
import { DocsThemeConfig } from 'nextra-theme-docs'

const config: DocsThemeConfig = {
  logo: <span><strong>KidneyAI</strong></span>,
  project: {
    link: 'https://github.com/shuding/nextra-docs-template',
  },
  docsRepositoryBase: 'https://github.com/shuding/nextra-docs-template',
  footer: {
    text: 'BMES Hackathon 2026 - Kidney Allocation Optimization',
  },
  useNextSeoProps() {
    return {
      titleTemplate: '%s – Organ Allocation Platform'
    }
  },
  head: (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="Intelligent Organ Allocation Platform" />
      <meta property="og:description" content="AI-assisted donor-recipient matching to improve organ utilization and reduce transplant waiting times" />
    </>
  ),
}

export default config
