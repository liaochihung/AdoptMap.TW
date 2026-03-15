import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// leaflet.markercluster is a legacy UMD bundle that references bare `L` as a
// global variable, but its CJS factory receives only `exports` — no L.
// This plugin rewrites the UMD wrapper so that the CJS branch also passes L,
// sourced from a proper `import L from 'leaflet'` that Rollup can resolve.
function leafletMarkerclusterPlugin() {
  return {
    name: 'leaflet-markercluster-fix',
    transform(code, id) {
      if (!id.includes('leaflet.markercluster') || !id.endsWith('.js')) return
      // The UMD wrapper:
      //   factory(exports)                  ← CJS branch, no L
      //   factory((global.Leaflet...))      ← browser branch, also no L
      // Rewrite to inject L into the factory call in all branches,
      // and prepend an import so Rollup knows to include leaflet first.
      const patched = code
        // CJS branch: factory(exports) → factory(exports, L)
        .replace('factory(exports)', 'factory(exports, L)')
        // AMD branch: define(['exports'], factory) → define(['exports', 'leaflet'], factory)
        .replace("define(['exports'], factory)", "define(['exports', 'leaflet'], factory)")
        // IIFE browser branch: factory((global.Leaflet...)) → factory((global.Leaflet...), global.L)
        .replace(/factory\((global\.Leaflet[^)]+)\)/, 'factory($1, global.L)')
        // factory signature: function (exports) → function (exports, L)
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
  build: {
    outDir: 'dist'
  },
})
