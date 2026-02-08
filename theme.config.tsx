import React from "react";
import { DocsThemeConfig } from "nextra-theme-docs";

const config: DocsThemeConfig = {
  logo: (
    <span>
      <strong>Match</strong>
    </span>
  ),
  project: {
    link: "https://github.com/KULDUDECS50/biohack-osu-2026",
  },
  docsRepositoryBase: "https://github.com/shuding/nextra-docs-template",
  footer: {
    content: <span>Match - ML-powered kidney allocation research</span>,
  },
};

export default config;
