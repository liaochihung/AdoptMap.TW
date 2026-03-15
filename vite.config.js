import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// leaflet.markercluster is a legacy UMD bundle that references bare `L` as a
// global variable, but its CJS factory receives only `exports` — no L.
// This plugin rewrites the UMD wrapper so that the CJS branch also passes L,
// sourced from a proper `import L from 'leaflet'` that Rollup can resolve.
function leafletMarkerclusterPlugin() {
  return {
    name: 'leaflet-markercluster-fix',
    enforce: 'pre',
    transform(code, id) {
      if (!id.includes('leaflet.markercluster') || !id.endsWith('.js')) return
      const patched = code
        .replace('factory(exports)', 'factory(exports, L)')
        .replace("define(['exports'], factory)", "define(['exports', 'leaflet'], factory)")
        .replace(/factory\((global\.Leaflet[^)]+)\)/, 'factory($1, global.L)')
        .replace('function (exports) {', 'function (exports, L) {')

      return {
        code: `import L from 'leaflet';\n${patched}`,
        map: null,
      }
    },
  }
}

export default defineConfig({
  plugins: [vue(), leafletMarkerclusterPlugin()],
  base: '/AdoptMap.TW/',
  optimizeDeps: {
    // Exclude from pre-bundling so our transform plugin can process it
    exclude: ['leaflet.markercluster'],
  },
  build: {
    outDir: 'dist'
  },
})
