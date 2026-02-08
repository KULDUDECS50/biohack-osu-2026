import nextra from 'nextra'

const withNextra = nextra({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.tsx',
})

export default withNextra({
  webpack: (config) => {
    config.resolve.fallback = {
      ...config.resolve.fallback,
      'supports-color': false,
    }
    return config
  },
})
