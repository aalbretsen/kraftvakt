import json from "@rollup/plugin-json";
import resolve from "@rollup/plugin-node-resolve";
import terser from "@rollup/plugin-terser";
import typescript from "@rollup/plugin-typescript";

export default {
  input: "src/kraftvakt-panel.ts",
  output: {
    file: "../custom_components/kraftvakt/frontend/kraftvakt-panel.js",
    format: "es",
  },
  plugins: [
    resolve(),
    json({ preferConst: true }),
    typescript({ noEmitOnError: true }),
    terser({ format: { comments: false } }),
  ],
};
