import React from "react";
import { DocsThemeConfig } from "nextra-theme-docs";

const config: DocsThemeConfig = {
  logo: (
    <span style={{ fontWeight: 700, fontSize: 18 }}>
      Match
    </span>
  ),
  project: {
    link: "https://github.com/KULDUDECS50/biohack-osu-2026",
  },
  docsRepositoryBase: "https://github.com/KULDUDECS50/biohack-osu-2026",
  footer: {
    content: (
      <span>
        Match &mdash; ML-powered kidney allocation research | BioHack 2026
      </span>
    ),
  },
  head: (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta name="description" content="Match - ML-powered kidney allocation to reduce organ waste" />
      <title>Match - Kidney Allocation Research</title>
    </>
  ),
  sidebar: {
    defaultMenuCollapseLevel: 1,
    toggleButton: true
  },
  toc: {
    float: true
  }
};

export default config;
