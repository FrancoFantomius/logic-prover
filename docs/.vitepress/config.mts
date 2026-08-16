import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Logic Prover',
  description: 'A formal logic theorem prover, explorer, deducer, and Lean 4 exporter in Python.',
  base: '/logic-prover/',
  cleanUrls: true,

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logic-prover/favicon.ico' }],
    ['meta', { name: 'theme-color', content: '#6366f1' }],
  ],

  themeConfig: {
    siteTitle: 'Logic Prover',
    logo: undefined,

    nav: [
      { text: 'Home', link: '/' },
      { text: 'Architecture', link: '/#architecture-overview' },
      { text: 'Examples', link: '/examples' },
      {
        text: 'API Reference',
        items: [
          { text: 'Core AST & Rewriting', link: '/api/core' },
          { text: 'Resolution Prover', link: '/api/prover' },
          { text: 'Formula Explorer', link: '/api/explorer' },
          { text: 'Hypothesis Deducer', link: '/api/deducer' },
          { text: 'Exporters & Visualizers', link: '/api/exporters' },
          { text: 'Knowledge Bases', link: '/api/kb' },
          { text: 'Second-Order Logic', link: '/api/sol' },
          { text: 'Configuration', link: '/api/config' },
          { text: 'Utilities', link: '/api/utils' },
        ],
      },
      {
        text: 'v0.1.4',
        items: [
          { text: 'Changelog', link: 'https://github.com/FrancoFantomius/logic-prover/blob/main/CHANGELOG.md' },
          { text: 'Contributing', link: 'https://github.com/FrancoFantomius/logic-prover/blob/main/CONTRIBUTING.md' },
          { text: 'Security', link: 'https://github.com/FrancoFantomius/logic-prover/blob/main/SECURITY.md' },
        ],
      },
    ],

    sidebar: [
      {
        text: 'Getting Started',
        items: [
          { text: 'Overview & Portal', link: '/' },
          { text: 'Examples & Tutorials', link: '/examples' },
        ],
      },
      {
        text: 'Core & Reasoning',
        items: [
          { text: 'Core AST & Rewriting', link: '/api/core' },
          { text: 'Resolution Theorem Prover', link: '/api/prover' },
          { text: 'Knowledge Bases', link: '/api/kb' },
          { text: 'Second-Order Logic (SOL)', link: '/api/sol' },
        ],
      },
      {
        text: 'Exploration & Analysis',
        items: [
          { text: 'Formula Explorer & Ranking', link: '/api/explorer' },
          { text: 'Hypothesis Deducer & Equivalence', link: '/api/deducer' },
        ],
      },
      {
        text: 'Exporters & System',
        items: [
          { text: 'Lean 4 & Graph Exporters', link: '/api/exporters' },
          { text: 'Configuration & Settings', link: '/api/config' },
          { text: 'Utilities & Doc Generator', link: '/api/utils' },
        ],
      },
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/FrancoFantomius/logic-prover' },
    ],

    search: {
      provider: 'local',
    },

    editLink: {
      pattern: 'https://github.com/FrancoFantomius/logic-prover/edit/main/docs/:path',
      text: 'Edit this page on GitHub',
    },

    footer: {
      message: 'Released under the CC BY-NC 4.0 License.',
      copyright: 'Copyright © 2026 Franco Fantomius',
    },
  },
})
